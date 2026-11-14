package com.kmkirk83.difrtoolkit

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

private val Bg = Color(0xFF101827)
private val Panel = Color(0xFF182438)
private val Ink = Color(0xFFE6EDF7)
private val Muted = Color(0xFFA9BAD1)
private val Accent = Color(0xFF56C9BE)
private val Bad = Color(0xFFFFB4AB)

private const val EXPECTED_UTC = "2026-01-01T00:00:00+00:00"

private data class SelfCheck(val utc: String?)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val appContext = applicationContext
        setContent {
            WorkbenchBaseline(appContext)
        }
    }
}

@Composable
private fun WorkbenchBaseline(context: Context) {
    var state by remember { mutableStateOf<Result<SelfCheck>?>(null) }
    LaunchedEffect(Unit) {
        state = runCatching { runSelfCheck(context) }
    }
    MaterialTheme(
        colorScheme = darkColorScheme(
            background = Bg,
            surface = Panel,
            primary = Accent,
            onBackground = Ink,
            onSurface = Ink,
        ),
    ) {
        Surface(modifier = Modifier.fillMaxSize(), color = Bg) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .systemBarsPadding()
                    .verticalScroll(rememberScrollState())
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                Text("DFIR Workbench", color = Ink, fontSize = 28.sp)
                Text(
                    "Shell 0.1.0 for repository DIFR-TOOLKIT. Embedded engine is DFIR Kit 0.2. Not a certified forensic product. This screen does not collect evidence and does not produce findings.",
                    color = Muted,
                )
                SelfCheckCard(state)
                UnavailableCard()
            }
        }
    }
}

@Composable
private fun SelfCheckCard(state: Result<SelfCheck>?) {
    Surface(color = Panel, modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Embedded kit self-check", color = Ink, fontSize = 18.sp)
            Text(
                "Calls dfir_kit.normalize on 2026-01-01T01:00:00+01:00. Expected UTC is $EXPECTED_UTC. This is the same conversion as the kit unit test, not a case result.",
                color = Muted,
            )
            when (state) {
                null -> Row {
                    CircularProgressIndicator(
                        color = Accent,
                        modifier = Modifier.semantics {
                            contentDescription = "Checking embedded DFIR kit"
                        },
                    )
                    Text(
                        "Loading Python and running normalize.",
                        color = Ink,
                        modifier = Modifier.padding(start = 12.dp),
                    )
                }
                else -> {
                    state.fold(
                        onSuccess = { check ->
                            val ok = check.utc == EXPECTED_UTC
                            Text(
                                if (ok) "Passed" else "Failed",
                                color = if (ok) Accent else Bad,
                                fontSize = 20.sp,
                            )
                            Text(
                                "time_utc = ${check.utc ?: "null"}",
                                color = Ink,
                                fontFamily = FontFamily.Monospace,
                            )
                            if (!ok) {
                                Text(
                                    "The embedded kit did not return the expected timestamp. Do not treat later output as the desktop kit until this matches.",
                                    color = Bad,
                                )
                            }
                        },
                        onFailure = { error ->
                            Text("Failed to start the kit", color = Bad, fontSize = 20.sp)
                            Text(
                                "${error.javaClass.simpleName}: ${error.message ?: "no message"}",
                                color = Ink,
                                fontFamily = FontFamily.Monospace,
                            )
                        },
                    )
                }
            }
        }
    }
}

@Composable
private fun UnavailableCard() {
    Surface(color = Panel, modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Not available on this phone", color = Ink, fontSize = 18.sp)
            Text("Windows collection. The kit refuses to run it unless the host is Windows.", color = Muted)
            Text("Host ADB collection and bugreport. Those commands drive a separate device from a computer. This app does not image this phone.", color = Muted)
            Text("age encryption and OpenSSL signatures. Those programs are not part of the kit and are not bundled.", color = Muted)
            Text("Entra and Workspace collection. Not in this build. No network permission is requested.", color = Muted)
            Text("Case init, import, timeline, and verify are the next slice, after this APK installs and the self-check passes.", color = Muted)
        }
    }
}

private suspend fun runSelfCheck(context: Context): SelfCheck = withContext(Dispatchers.Default) {
    if (!Python.isStarted()) {
        Python.start(AndroidPlatform(context))
    }
    val py = Python.getInstance()
    val row = py.getModule("json").callAttr(
        "loads",
        """{"time":"2026-01-01T01:00:00+01:00"}""",
    )
    val result = py.getModule("dfir_kit").callAttr("normalize", row)
    val utc = result.callAttr("get", "time_utc").toJava(String::class.java)
    SelfCheck(utc = utc)
}
