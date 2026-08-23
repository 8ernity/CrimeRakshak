package com.example.crimerakshak

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.example.crimerakshak.theme.CrimeRakshakTheme

import androidx.compose.runtime.LaunchedEffect
import com.example.crimerakshak.api.RetrofitClient
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            LaunchedEffect(Unit) {
                try {
                    val response = RetrofitClient.apiService.login("admin", "admin123")
                    RetrofitClient.authToken = response.accessToken
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
            
            CrimeRakshakTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MainNavigation()
                }
            }
        }
    }
}
