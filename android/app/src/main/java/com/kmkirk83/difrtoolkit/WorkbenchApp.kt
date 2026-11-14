package com.kmkirk83.difrtoolkit

import android.content.Context
import android.provider.Settings
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.path
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.animation.core.animateFloatAsState
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

private val Bg = Color(0xFF0B1220)
private val Rail = Color(0xFF142033)
private val Nav = Color(0xFF101827)
private val Card = Color(0xFF182438)
private val Ink = Color(0xFFE6EDF7)
private val Secondary = Color(0xFFA9BAD1)
private val Faint = Color(0xFF8AA0B8)
private val Accent = Color(0xFF56C9BE)
private val Break = Color(0xFFFFB4AB)
private val Hairline = Color(0xFF243246)

private val Sans = FontFamily(
    Font(R.font.ibm_plex_sans_regular, FontWeight.Normal),
    Font(R.font.ibm_plex_sans_medium, FontWeight.Medium),
)
private val Mono = FontFamily(Font(R.font.ibm_plex_mono_regular, FontWeight.Normal))

private const val EXPECTED_UTC = "2026-01-01T00:00:00+00:00"

private enum class Tab(val label: String) {
    Case("Case"),
    Collect("Collect"),
    Timeline("Timeline"),
    Log("Log"),
}

private data class SelfCheck(val utc: String?)

private data class Blocked(val title: String, val meta: String, val detail: String)

private val collectBlocked = listOf(
    Blocked(
        "Windows collection",
        "Unavailable on this phone",
        "The kit runs this only when the host is Windows. It calls PowerShell, wevtutil, and other Windows commands. This phone cannot run that collection.",
    ),
    Blocked(
        "ADB and bugreport",
        "Needs a computer",
        "The kit android command is host adb against a different device. It does not inspect this phone, and this app does not image this phone.",
    ),
)

private val caseBlocked = listOf(
    Blocked(
        "age and OpenSSL",
        "Programs are not bundled",
        "Encryption and signatures shell out to age and openssl. Those programs are not in this APK. A passphrase prompt is not supported.",
    ),
    Blocked(
        "Entra and Workspace",
        "Not in this build",
        "Account collection needs a short-lived token and a network call. This build does not request network access and does not collect account records.",
    ),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WorkbenchApp(context: Context) {
    var check by remember { mutableStateOf<Result<SelfCheck>?>(null) }
    LaunchedEffect(Unit) {
        check = runCatching { runSelfCheck(context) }
    }
    val passed = check?.getOrNull()?.utc == EXPECTED_UTC
    var reducePref by rememberSaveable { mutableStateOf(false) }
    val systemReduce = systemReduceMotion(context)
    val reduce = reducePref || systemReduce
    var tabName by rememberSaveable { mutableStateOf(Tab.Case.name) }
    val tab = Tab.valueOf(tabName)
    var sheet by remember { mutableStateOf<Blocked?>(null) }
    var utc by remember { mutableStateOf(formatUtc()) }
    LaunchedEffect(Unit) {
        while (true) {
            utc = formatUtc()
            delay(1000)
        }
    }
    var lineTarget by remember { mutableFloatStateOf(0f) }
    LaunchedEffect(passed) {
        if (passed) lineTarget = 1f
    }
    val line by animateFloatAsState(
        targetValue = lineTarget,
        animationSpec = tween(durationMillis = if (reduce) 0 else 240),
        label = "railLine",
    )

    MaterialTheme(
        colorScheme = darkColorScheme(
            background = Bg,
            surface = Card,
            primary = Accent,
            onBackground = Ink,
            onSurface = Ink,
        ),
    ) {
        Box(Modifier.fillMaxSize().background(Bg)) {
            InstrumentGrid(Modifier.fillMaxSize())
            Column(Modifier.fillMaxSize()) {
                StatusRail(
                    modifier = Modifier.statusBarsPadding(),
                    left = if (passed) "CASE" else "KIT",
                    center = if (passed) "IDLE" else if (check == null) "IDLE" else "UNAVAILABLE",
                    utc = utc,
                    line = line,
                )
                if (!passed) {
                    StopOrLoading(check, Modifier.weight(1f))
                } else {
                    val rise = with(LocalDensity.current) { 8.dp.roundToPx() }
                    AnimatedContent(
                        targetState = tab,
                        modifier = Modifier.weight(1f),
                        transitionSpec = {
                            if (reduce) {
                                fadeIn(tween(120)) togetherWith fadeOut(tween(120))
                            } else {
                                (fadeIn(tween(200)) + slideInVertically(tween(200)) { rise }) togetherWith
                                    fadeOut(tween(120))
                            }
                        },
                        label = "tab",
                    ) { current ->
                        Column(
                            Modifier
                                .fillMaxSize()
                                .verticalScroll(rememberScrollState())
                                .padding(horizontal = 20.dp, vertical = 16.dp),
                            verticalArrangement = Arrangement.spacedBy(16.dp),
                        ) {
                            when (current) {
                                Tab.Case -> CaseTab(onBlocked = { sheet = it })
                                Tab.Collect -> CollectTab(onBlocked = { sheet = it })
                                Tab.Timeline -> TimelineTab()
                                Tab.Log -> LogTab(
                                    reducePref = reducePref,
                                    systemReduce = systemReduce,
                                    onReducePref = { reducePref = it },
                                )
                            }
                        }
                    }
                    WorkbenchNav(tab) { tabName = it.name }
                }
            }
        }
        val open = sheet
        if (open != null) {
            ModalBottomSheet(
                onDismissRequest = { sheet = null },
                containerColor = Card,
            ) {
                Column(
                    Modifier.padding(start = 20.dp, end = 20.dp, bottom = 28.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text("Unavailable", color = Faint, fontFamily = Mono, fontSize = 13.sp)
                    Text(open.title, color = Ink, fontFamily = Sans, fontWeight = FontWeight.Medium, fontSize = 22.sp)
                    Text(open.detail, color = Secondary, fontFamily = Sans, fontSize = 15.sp)
                    Text("Nothing is started from this sheet.", color = Ink, fontFamily = Sans, fontSize = 15.sp)
                }
            }
        }
    }
}

@Composable
private fun StatusRail(modifier: Modifier, left: String, center: String, utc: String, line: Float) {
    Column(
        modifier
            .fillMaxWidth()
            .background(Rail)
            .semantics { contentDescription = "Status $left, $center, $utc UTC" },
    ) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(left, color = Secondary, fontFamily = Mono, fontSize = 12.sp)
            Text(center, color = Secondary, fontFamily = Mono, fontSize = 12.sp)
            Text(utc, color = Secondary, fontFamily = Mono, fontSize = 12.sp)
        }
        Box(Modifier.fillMaxWidth().height(2.dp).background(Hairline)) {
            Box(Modifier.fillMaxHeight().fillMaxWidth(line.coerceIn(0f, 1f)).background(Accent))
        }
    }
}

@Composable
private fun StopOrLoading(check: Result<SelfCheck>?, modifier: Modifier) {
    Column(
        modifier
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("DFIR Workbench", color = Ink, fontFamily = Sans, fontWeight = FontWeight.Medium, fontSize = 22.sp)
        when (check) {
            null -> Row(verticalAlignment = Alignment.CenterVertically) {
                CircularProgressIndicator(
                    color = Accent,
                    modifier = Modifier.semantics { contentDescription = "Checking embedded DFIR kit" },
                )
                Text(
                    "Loading Python and running normalize.",
                    color = Ink,
                    fontFamily = Sans,
                    fontSize = 15.sp,
                    modifier = Modifier.padding(start = 12.dp),
                )
            }
            else -> check.fold(
                onSuccess = { result ->
                    Text("Self-check failed", color = Break, fontFamily = Sans, fontWeight = FontWeight.Medium, fontSize = 22.sp)
                    Text(
                        "time_utc = ${result.utc ?: "null"}. Expected $EXPECTED_UTC. Later screens stay closed until this matches the kit unit test.",
                        color = Ink,
                        fontFamily = Mono,
                        fontSize = 13.sp,
                    )
                },
                onFailure = { error ->
                    Text("Kit did not start", color = Break, fontFamily = Sans, fontWeight = FontWeight.Medium, fontSize = 22.sp)
                    Text(
                        "${error.javaClass.simpleName}: ${error.message ?: "no message"}",
                        color = Ink,
                        fontFamily = Mono,
                        fontSize = 13.sp,
                    )
                },
            )
        }
    }
}

@Composable
private fun CaseTab(onBlocked: (Blocked) -> Unit) {
    Text("Cases", color = Ink, fontFamily = Sans, fontWeight = FontWeight.Medium, fontSize = 22.sp)
    Text("On this phone. Nothing is uploaded.", color = Secondary, fontFamily = Sans, fontSize = 15.sp)
    Surface(color = Card, modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.height(androidx.compose.foundation.layout.IntrinsicSize.Min)) {
            Box(Modifier.width(3.dp).fillMaxHeight().background(Accent))
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("No case yet", color = Ink, fontFamily = Sans, fontWeight = FontWeight.Medium, fontSize = 18.sp)
                Text(
                    "Creating a case is not in this build. No folder is created and no file is copied.",
                    color = Secondary,
                    fontFamily = Sans,
                    fontSize = 15.sp,
                )
            }
        }
    }
    Text("Shell 0.1.1 · Kit 0.2 · self-check passed", color = Faint, fontFamily = Mono, fontSize = 13.sp)
    BlockedGroup(caseBlocked, onBlocked)
}

@Composable
private fun CollectTab(onBlocked: (Blocked) -> Unit) {
    Text("Collect", color = Ink, fontFamily = Sans, fontWeight = FontWeight.Medium, fontSize = 22.sp)
    Text("Copy only files you choose. Originals are not modified.", color = Secondary, fontFamily = Sans, fontSize = 15.sp)
    Surface(color = Card, modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Import files", color = Ink, fontFamily = Sans, fontWeight = FontWeight.Medium, fontSize = 18.sp)
            Text(
                "Not in this build. When it is, SHA-256 is recorded before and after a copy you choose.",
                color = Secondary,
                fontFamily = Sans,
                fontSize = 15.sp,
            )
        }
    }
    BlockedGroup(collectBlocked, onBlocked)
}

@Composable
private fun TimelineTab() {
    Text("Timeline", color = Ink, fontFamily = Sans, fontWeight = FontWeight.Medium, fontSize = 22.sp)
    Text("Canonical CSV only. Not a verdict.", color = Secondary, fontFamily = Sans, fontSize = 15.sp)
    Surface(color = Card, modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("No timeline yet", color = Ink, fontFamily = Sans, fontWeight = FontWeight.Medium, fontSize = 18.sp)
            Text(
                "Analysis is not in this build. A later CSV must use these columns. No sample incidents are loaded.",
                color = Secondary,
                fontFamily = Sans,
                fontSize = 15.sp,
            )
            Text(
                "time\nsource\nevent_id\nrecord_id\ndescription\nuncertainty_seconds\nclock_offset_seconds",
                color = Faint,
                fontFamily = Mono,
                fontSize = 13.sp,
            )
        }
    }
}

@Composable
private fun LogTab(reducePref: Boolean, systemReduce: Boolean, onReducePref: (Boolean) -> Unit) {
    Text("Log", color = Ink, fontFamily = Sans, fontWeight = FontWeight.Medium, fontSize = 22.sp)
    Text("No case operations yet.", color = Secondary, fontFamily = Sans, fontSize = 15.sp)
    Text(
        "self-check time_utc $EXPECTED_UTC",
        color = Ink,
        fontFamily = Mono,
        fontSize = 13.sp,
    )
    Text(
        "The case journal is the record once a case exists. This screen does not show one.",
        color = Secondary,
        fontFamily = Sans,
        fontSize = 15.sp,
    )
    Surface(color = Card, modifier = Modifier.fillMaxWidth()) {
        Row(
            Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Reduce motion", color = Ink, fontFamily = Sans, fontSize = 16.sp)
                Text(
                    "Stops the rail line and the tab slide. The clock still updates.",
                    color = Secondary,
                    fontFamily = Sans,
                    fontSize = 15.sp,
                )
            }
            Switch(
                checked = reducePref || systemReduce,
                onCheckedChange = onReducePref,
                enabled = !systemReduce,
                colors = SwitchDefaults.colors(
                    checkedTrackColor = Accent,
                    checkedThumbColor = Ink,
                    uncheckedTrackColor = Hairline,
                    uncheckedThumbColor = Secondary,
                ),
                modifier = Modifier.semantics { contentDescription = "Reduce motion" },
            )
        }
    }
    if (systemReduce) {
        Text(
            "Android is already reducing motion. This switch cannot turn that off.",
            color = Secondary,
            fontFamily = Sans,
            fontSize = 15.sp,
        )
    }
}

@Composable
private fun BlockedGroup(items: List<Blocked>, onBlocked: (Blocked) -> Unit) {
    Surface(color = Card, modifier = Modifier.fillMaxWidth()) {
        Column {
            items.forEachIndexed { index, item ->
                if (index > 0) HorizontalDivider(color = Hairline)
                Row(
                    Modifier
                        .fillMaxWidth()
                        .clickable(onClickLabel = "Explain why this is unavailable") { onBlocked(item) }
                        .padding(16.dp)
                        .semantics { contentDescription = "${item.title}. Unavailable. ${item.meta}" },
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    SlashMark()
                    Column(Modifier.padding(start = 12.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(item.title, color = Ink, fontFamily = Sans, fontSize = 16.sp)
                        Text("Unavailable · ${item.meta}", color = Faint, fontFamily = Mono, fontSize = 13.sp)
                    }
                }
            }
        }
    }
}

@Composable
private fun WorkbenchNav(selected: Tab, onSelect: (Tab) -> Unit) {
    NavigationBar(containerColor = Nav, contentColor = Faint) {
        Tab.entries.forEach { tab ->
            val isSelected = tab == selected
            NavigationBarItem(
                selected = isSelected,
                onClick = { onSelect(tab) },
                icon = {
                    Icon(
                        imageVector = iconFor(tab),
                        contentDescription = null,
                    )
                },
                label = { Text(tab.label, fontFamily = Sans, fontSize = 12.sp) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = Accent,
                    selectedTextColor = Accent,
                    unselectedIconColor = Faint,
                    unselectedTextColor = Faint,
                    indicatorColor = Color(0xFF1C3A38),
                ),
                modifier = Modifier.semantics { contentDescription = tab.label },
            )
        }
    }
}

@Composable
private fun InstrumentGrid(modifier: Modifier) {
    Canvas(modifier) {
        val step = 32.dp.toPx()
        val color = Color.White.copy(alpha = 0.04f)
        var x = 0f
        while (x <= size.width) {
            drawLine(color, Offset(x, 0f), Offset(x, size.height), strokeWidth = 1f)
            x += step
        }
        var y = 0f
        while (y <= size.height) {
            drawLine(color, Offset(0f, y), Offset(size.width, y), strokeWidth = 1f)
            y += step
        }
    }
}

@Composable
private fun SlashMark() {
    Canvas(Modifier.width(20.dp).height(20.dp).semantics { contentDescription = "Unavailable" }) {
        val color = Faint
        drawCircle(color = color, radius = size.minDimension / 2f - 1f, style = androidx.compose.ui.graphics.drawscope.Stroke(width = 1.5f))
        drawLine(
            color = color,
            start = Offset(size.width * 0.28f, size.height * 0.72f),
            end = Offset(size.width * 0.72f, size.height * 0.28f),
            strokeWidth = 1.5f,
            cap = StrokeCap.Round,
        )
    }
}

private fun iconFor(tab: Tab): ImageVector = when (tab) {
    Tab.Case -> caseIcon
    Tab.Collect -> collectIcon
    Tab.Timeline -> timelineIcon
    Tab.Log -> logIcon
}

private fun lineIcon(name: String, draw: androidx.compose.ui.graphics.vector.PathBuilder.() -> Unit): ImageVector {
    return ImageVector.Builder(
        name = name,
        defaultWidth = 24.dp,
        defaultHeight = 24.dp,
        viewportWidth = 24f,
        viewportHeight = 24f,
    ).apply {
        path(
            stroke = SolidColor(Color.Black),
            strokeLineWidth = 1.6f,
            strokeLineCap = StrokeCap.Round,
            strokeLineJoin = StrokeJoin.Round,
        ) {
            draw()
        }
    }.build()
}

private val caseIcon = lineIcon("case") {
    moveTo(4f, 8f)
    lineTo(9f, 8f)
    lineTo(11f, 10f)
    lineTo(20f, 10f)
    lineTo(20f, 18f)
    lineTo(4f, 18f)
    close()
}

private val collectIcon = lineIcon("collect") {
    moveTo(12f, 4f)
    lineTo(12f, 14f)
    moveTo(8f, 10f)
    lineTo(12f, 14f)
    lineTo(16f, 10f)
    moveTo(5f, 18f)
    lineTo(19f, 18f)
}

private val timelineIcon = lineIcon("timeline") {
    moveTo(6f, 7f)
    lineTo(20f, 7f)
    moveTo(6f, 12f)
    lineTo(20f, 12f)
    moveTo(6f, 17f)
    lineTo(14f, 17f)
    moveTo(4f, 7f)
    lineTo(4.1f, 7f)
    moveTo(4f, 12f)
    lineTo(4.1f, 12f)
    moveTo(4f, 17f)
    lineTo(4.1f, 17f)
}

private val logIcon = lineIcon("log") {
    moveTo(5f, 6f)
    lineTo(19f, 6f)
    moveTo(5f, 12f)
    lineTo(19f, 12f)
    moveTo(5f, 18f)
    lineTo(13f, 18f)
}

@Composable
private fun systemReduceMotion(context: Context): Boolean {
    val scale = Settings.Global.getFloat(
        context.contentResolver,
        Settings.Global.ANIMATOR_DURATION_SCALE,
        1f,
    )
    return scale == 0f
}

private fun formatUtc(): String {
    val format = SimpleDateFormat("HH:mm:ss", Locale.US)
    format.timeZone = TimeZone.getTimeZone("UTC")
    return format.format(Date())
}

private suspend fun runSelfCheck(context: Context): SelfCheck = withContext(Dispatchers.Default) {
    if (!Python.isStarted()) {
        Python.start(AndroidPlatform(context))
    }
    val py = Python.getInstance()
    val row = py.getModule("json").callAttr(
        "loads",
        "{\"time\":\"2026-01-01T01:00:00+01:00\"}",
    )
    val result = py.getModule("dfir_kit").callAttr("normalize", row)
    SelfCheck(utc = result.callAttr("get", "time_utc").toJava(String::class.java))
}
