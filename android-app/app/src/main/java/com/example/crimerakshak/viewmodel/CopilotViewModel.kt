package com.example.crimerakshak.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.crimerakshak.api.ChatRequest
import com.example.crimerakshak.api.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.UUID

data class ChatMessage(
    val id: String = UUID.randomUUID().toString(),
    val text: String,
    val isUser: Boolean,
    val isLoading: Boolean = false
)

data class CopilotState(
    val messages: List<ChatMessage> = listOf(
        ChatMessage(
            text = "Welcome to Tactical Command, Officer.\nI have access to the full CrimeRakshak intelligence network.",
            isUser = false
        )
    ),
    val conversationId: String? = null,
    val isListening: Boolean = false,
    val inputText: String = ""
)

class CopilotViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(CopilotState())
    val uiState: StateFlow<CopilotState> = _uiState.asStateFlow()

    fun onInputTextChanged(text: String) {
        _uiState.value = _uiState.value.copy(inputText = text)
    }

    fun toggleListening(isListening: Boolean) {
        _uiState.value = _uiState.value.copy(isListening = isListening)
    }

    fun sendMessage(text: String) {
        if (text.isBlank()) return

        // Add user message
        val currentMessages = _uiState.value.messages.toMutableList()
        currentMessages.add(ChatMessage(text = text, isUser = true))
        
        // Add loading message
        val loadingMessage = ChatMessage(text = "...", isUser = false, isLoading = true)
        currentMessages.add(loadingMessage)
        
        _uiState.value = _uiState.value.copy(
            messages = currentMessages,
            inputText = ""
        )

        viewModelScope.launch {
            try {
                val request = ChatRequest(
                    message = text,
                    conversationId = _uiState.value.conversationId,
                    language = "en"
                )
                
                val response = RetrofitClient.apiService.chat(request)
                
                // Remove loading message and add response
                val updatedMessages = _uiState.value.messages.filter { !it.isLoading }.toMutableList()
                updatedMessages.add(ChatMessage(text = response.answer, isUser = false))
                
                _uiState.value = _uiState.value.copy(
                    messages = updatedMessages,
                    conversationId = response.conversationId
                )
            } catch (e: Exception) {
                e.printStackTrace()
                // Remove loading message and add error
                val updatedMessages = _uiState.value.messages.filter { !it.isLoading }.toMutableList()
                updatedMessages.add(ChatMessage(text = "Error connecting to AI Command.", isUser = false))
                
                _uiState.value = _uiState.value.copy(
                    messages = updatedMessages
                )
            }
        }
    }
}
