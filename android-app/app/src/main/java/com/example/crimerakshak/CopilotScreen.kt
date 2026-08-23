package com.example.crimerakshak

import android.Manifest
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.crimerakshak.viewmodel.CopilotViewModel
import com.example.crimerakshak.viewmodel.ChatMessage
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Stop
import androidx.compose.foundation.border
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.SmartToy

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CopilotScreen(
    viewModel: CopilotViewModel = viewModel()
) {
    val state by viewModel.uiState.collectAsState()
    var query by remember { mutableStateOf("") }
    var isListening by remember { mutableStateOf(false) }
    val context = LocalContext.current
    
    val speechRecognizer = remember { SpeechRecognizer.createSpeechRecognizer(context) }
    
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            startListening(speechRecognizer, { isListening = true }, { isListening = false }, { query = it })
        } else {
            Log.e("CopilotScreen", "Audio permission denied")
        }
    }
    
    DisposableEffect(Unit) {
        onDispose {
            speechRecognizer.destroy()
        }
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(BackgroundDark)
            .padding(16.dp)
    ) {
        // Header
        Row(
            modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.SmartToy, contentDescription = null, tint = PrimaryGreen)
                Spacer(modifier = Modifier.width(8.dp))
                Text("AI COPILOT", color = PrimaryGreen, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            }
            Icon(Icons.Filled.History, contentDescription = null, tint = TextMuted)
        }

        // Chat Area
        androidx.compose.foundation.lazy.LazyColumn(
            modifier = Modifier.weight(1f).fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            items(state.messages.size) { index ->
                val message = state.messages[index]
                if (message.isUser) {
                    Column(modifier = Modifier.fillMaxWidth(), horizontalAlignment = Alignment.End) {
                        Text("OFFICER 402", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 8.dp))
                        Row {
                            Spacer(modifier = Modifier.weight(0.1f))
                            Box(modifier = Modifier.weight(0.9f).background(SurfaceDark, RoundedCornerShape(12.dp)).border(1.dp, PrimaryGreen, RoundedCornerShape(12.dp)).padding(16.dp)) {
                                Text(message.text, color = TextLight, fontSize = 16.sp)
                            }
                        }
                    }
                } else {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(bottom = 8.dp)) {
                            Icon(Icons.Filled.SmartToy, contentDescription = null, tint = TextMuted, modifier = Modifier.size(14.dp))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("TACTICAL AI", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        }
                        Box(modifier = Modifier.background(SurfaceDark, RoundedCornerShape(12.dp)).padding(16.dp)) {
                            Text(message.text, color = TextLight, fontSize = 16.sp)
                        }
                    }
                }
            }
        }
        
        // Input Area
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 16.dp, bottom = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            FloatingActionButton(
                onClick = {
                    if (isListening) {
                        speechRecognizer.stopListening()
                        isListening = false
                    } else {
                        permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                    }
                },
                containerColor = if (isListening) Color(0xFFffb4ab) else PrimaryGreen,
                shape = CircleShape
            ) {
                Icon(
                    if (isListening) Icons.Filled.Stop else Icons.Filled.Mic,
                    contentDescription = "Voice Input", 
                    tint = BackgroundDark
                )
            }
            Spacer(modifier = Modifier.width(8.dp))
            TextField(
                value = query,
                onValueChange = { query = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text(if (isListening) "Listening..." else "Message Tactical AI...") },
                shape = RoundedCornerShape(24.dp),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = SurfaceDark,
                    unfocusedContainerColor = SurfaceDark,
                    focusedTextColor = TextLight,
                    unfocusedTextColor = TextLight,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent,
                    disabledIndicatorColor = Color.Transparent,
                    disabledTextColor = TextMuted,
                    focusedPlaceholderColor = TextMuted,
                    unfocusedPlaceholderColor = TextMuted
                )
            )
            Spacer(modifier = Modifier.width(8.dp))
            FloatingActionButton(
                onClick = {
                    if (query.isNotBlank()) {
                        viewModel.sendMessage(query)
                        query = ""
                    }
                },
                containerColor = SurfaceDark,
                shape = CircleShape
            ) {
                Icon(Icons.Filled.Send, contentDescription = "Send", tint = TextMuted)
            }
        }
    }
}

private fun startListening(
    speechRecognizer: SpeechRecognizer,
    onStart: () -> Unit,
    onStop: () -> Unit,
    onResult: (String) -> Unit
) {
    val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
        putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
    }
    
    speechRecognizer.setRecognitionListener(object : RecognitionListener {
        override fun onReadyForSpeech(params: Bundle?) { onStart() }
        override fun onBeginningOfSpeech() {}
        override fun onRmsChanged(rmsdB: Float) {}
        override fun onBufferReceived(buffer: ByteArray?) {}
        override fun onEndOfSpeech() { onStop() }
        override fun onError(error: Int) {
            Log.e("CopilotScreen", "Speech recognition error: $error")
            onStop()
        }
        override fun onResults(results: Bundle?) {
            val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            if (!matches.isNullOrEmpty()) {
                onResult(matches[0])
            }
            onStop()
        }
        override fun onPartialResults(partialResults: Bundle?) {}
        override fun onEvent(eventType: Int, params: Bundle?) {}
    })
    
    speechRecognizer.startListening(intent)
}
