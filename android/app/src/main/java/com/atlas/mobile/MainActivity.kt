package com.atlas.mobile

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private val executor = Executors.newSingleThreadExecutor()
    private lateinit var symbolInput: EditText
    private lateinit var analyzeButton: Button
    private lateinit var statusView: TextView
    private lateinit var resultView: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(11, 18, 32)
        window.navigationBarColor = Color.rgb(11, 18, 32)
        if (!Python.isStarted()) Python.start(AndroidPlatform(this))

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(20, 22, 20, 16)
            setBackgroundColor(Color.rgb(11, 18, 32))
        }
        val title = TextView(this).apply {
            text = "ATLAS"
            textSize = 27f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER_VERTICAL
        }
        val subtitle = TextView(this).apply {
            text = "SMART MONEY ANALYSIS"
            textSize = 11f
            setTextColor(Color.rgb(148, 163, 184))
        }
        symbolInput = EditText(this).apply {
            hint = "Coin: BTC, ETH, SOL..."
            setSingleLine(true)
            setText("BTC")
            textSize = 17f
            setTextColor(Color.WHITE)
            setHintTextColor(Color.GRAY)
            setPadding(16, 8, 16, 8)
            setBackgroundColor(Color.rgb(30, 41, 59))
        }
        analyzeButton = Button(this).apply {
            text = "ANALİZ ET"
            isAllCaps = false
            textSize = 16f
        }
        statusView = TextView(this).apply {
            text = "Hazır • Bybit piyasa verisi"
            textSize = 13f
            setTextColor(Color.rgb(56, 189, 248))
            setPadding(0, 12, 0, 12)
        }
        resultView = TextView(this).apply {
            text = "Analiz için bir coin gir."
            textSize = 13f
            setTextColor(Color.rgb(226, 232, 240))
            setTextIsSelectable(true)
            setPadding(14, 14, 14, 14)
            setBackgroundColor(Color.rgb(17, 27, 45))
        }
        val scroll = ScrollView(this).apply {
            addView(resultView)
        }
        root.addView(title)
        root.addView(subtitle)
        root.addView(symbolInput, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT
        ).apply { topMargin = 22 })
        root.addView(analyzeButton, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT
        ).apply { topMargin = 10 })
        root.addView(statusView)
        root.addView(scroll, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f
        ))
        setContentView(root)

        analyzeButton.setOnClickListener { runAnalysis() }
    }

    private fun runAnalysis() {
        val symbol = symbolInput.text.toString().trim()
        if (symbol.isBlank()) {
            statusView.text = "Coin sembolü gir."
            return
        }
        analyzeButton.isEnabled = false
        statusView.text = "$symbol analiz ediliyor..."
        resultView.text = "Bybit verileri alınıyor. Stratejiler çalıştırılıyor..."
        executor.execute {
            val output = try {
                val py = Python.getInstance()
                val bridge = py.getModule("atlas_mobile")
                bridge.callAttr("set_data_dir", filesDir.absolutePath)
                bridge.callAttr("analyze", symbol).toString()
            } catch (e: Exception) {
                "Uygulama hatası: ${e.message}"
            }
            runOnUiThread {
                resultView.text = output
                statusView.text = if (output.contains("\"ok\": true")) "Analiz tamamlandı" else "Analiz tamamlanamadı"
                analyzeButton.isEnabled = true
            }
        }
    }

    override fun onDestroy() {
        executor.shutdown()
        super.onDestroy()
    }
}
