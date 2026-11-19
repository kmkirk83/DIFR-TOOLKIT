package com.kmkirk83.difrtoolkit

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import com.chaquo.python.PyException
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

data class CaseSummary(val path: String, val folder: String, val collector: String)

data class ImportRecord(
    val destination: String,
    val copyHash: String,
    val sourceChanged: Boolean,
)

data class CaseSnapshot(
    val path: String,
    val folder: String,
    val collector: String,
    val created: String,
    val version: String,
    val mismatch: Boolean,
    val verifyDetail: String?,
    val imports: List<ImportRecord>,
    val journalTail: List<String>,
)

private const val PREFS = "workbench"
private const val OPEN_CASE = "open_case"

fun casesRoot(context: Context): File = File(context.filesDir, "cases")

fun rememberOpenCase(context: Context, path: String?) {
    context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        .edit()
        .putString(OPEN_CASE, path)
        .apply()
}

fun savedOpenCase(context: Context): String? {
    return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(OPEN_CASE, null)
}

fun listCases(context: Context): List<CaseSummary> {
    val root = casesRoot(context)
    val dirs = root.listFiles { file -> file.isDirectory && File(file, "case.json").isFile } ?: return emptyList()
    return dirs.sortedByDescending { it.name }.map { dir ->
        val collector = try {
            JSONObject(File(dir, "case.json").readText()).optString("collector", "")
        } catch (_: Exception) {
            ""
        }
        CaseSummary(dir.absolutePath, dir.name, collector)
    }
}

fun planCaseDirectory(context: Context): File {
    val stamp = SimpleDateFormat("yyyyMMdd-HHmmss-SSS", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }.format(Date())
    return File(casesRoot(context), "case-$stamp")
}

suspend fun createCase(context: Context, directory: File, collector: String) {
    withContext(Dispatchers.Default) {
        val root = casesRoot(context).canonicalFile
        val target = directory.canonicalFile
        if (target.parentFile?.canonicalFile != root) {
            error("Case folder must stay in app storage.")
        }
        startPython(context)
        runKit(listOf("init", target.absolutePath, "--collector", collector.trim(), "--consent"))
    }
}

suspend fun importStaged(context: Context, caseDir: File, uris: List<Uri>, onStatus: (String) -> Unit): Int {
    val batch = File(File(context.cacheDir, "import-stage"), java.util.UUID.randomUUID().toString())
    val staged = ArrayList<File>(uris.size)
    return try {
        withContext(Dispatchers.IO) {
            uris.forEachIndexed { index, uri ->
                withContext(Dispatchers.Main) {
                    onStatus("Copying ${index + 1} of ${uris.size} into private staging. The original is not written.")
                }
                staged += stageCopy(context, uri, batch)
            }
            withContext(Dispatchers.Main) { onStatus("Running kit import.") }
            startPython(context)
            runKit(listOf("import", caseDir.absolutePath) + staged.map { it.absolutePath })
        }
        staged.size
    } finally {
        batch.deleteRecursively()
    }
}

suspend fun loadSnapshot(context: Context, directory: File): CaseSnapshot = withContext(Dispatchers.Default) {
    startPython(context)
    var detail: String? = null
    val mismatch = try {
        !verifyCase(directory)
    } catch (error: PyException) {
        detail = error.message?.trim()?.take(500)
        true
    }
    readSnapshot(directory, mismatch, detail)
}

private fun readSnapshot(directory: File, mismatch: Boolean, verifyDetail: String?): CaseSnapshot {
    val caseJson = JSONObject(File(directory, "case.json").readText())
    val journalFile = File(directory, "journal.jsonl")
    val lines = if (journalFile.isFile) journalFile.readLines() else emptyList()
    val imports = lines.mapNotNull { line ->
        try {
            val obj = JSONObject(line)
            if (obj.optString("action") != "import") return@mapNotNull null
            ImportRecord(
                destination = obj.optString("destination"),
                copyHash = obj.optString("copy_hash"),
                sourceChanged = obj.optBoolean("source_changed"),
            )
        } catch (_: Exception) {
            null
        }
    }
    return CaseSnapshot(
        path = directory.absolutePath,
        folder = directory.name,
        collector = caseJson.optString("collector"),
        created = caseJson.optString("created"),
        version = caseJson.optString("version"),
        mismatch = mismatch,
        verifyDetail = verifyDetail,
        imports = imports,
        journalTail = lines.takeLast(40),
    )
}

private fun startPython(context: Context) {
    if (!Python.isStarted()) {
        Python.start(AndroidPlatform(context))
    }
}

private fun runKit(args: List<String>) {
    val py = Python.getInstance()
    val argv = py.builtins.callAttr("list")
    for (arg in args) {
        argv.callAttr("append", arg)
    }
    py.getModule("difr_phone").callAttr("run", argv)
}

private fun verifyCase(directory: File): Boolean {
    val py = Python.getInstance()
    val path = py.getModule("pathlib").callAttr("Path", directory.absolutePath)
    return py.getModule("dfir_kit").callAttr("verify", path).toJava(Boolean::class.java) == true
}

private fun stageCopy(context: Context, uri: Uri, stageRoot: File): File {
    stageRoot.mkdirs()
    val display = displayName(context, uri)
    val safe = display.substringAfterLast('/').replace(Regex("[^A-Za-z0-9._-]"), "_").trim('_').ifBlank { "file" }.take(80)
    var dest = File(stageRoot, safe)
    var n = 2
    while (dest.exists()) {
        dest = File(stageRoot, "${safe}_$n")
        n += 1
    }
    context.contentResolver.openInputStream(uri)?.use { input ->
        dest.outputStream().use { output -> input.copyTo(output) }
    } ?: error("Could not read the selected file.")
    return dest
}

private fun displayName(context: Context, uri: Uri): String {
    val cursor = context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)
    cursor?.use {
        if (it.moveToFirst()) {
            val index = it.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if (index >= 0) {
                val name = it.getString(index)
                if (!name.isNullOrBlank()) return name
            }
        }
    }
    return uri.lastPathSegment ?: "file"
}
