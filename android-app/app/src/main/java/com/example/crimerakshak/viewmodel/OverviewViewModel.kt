package com.example.crimerakshak.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.crimerakshak.api.DistrictAnalytics
import com.example.crimerakshak.api.HotspotAnalytics
import com.example.crimerakshak.api.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class OverviewState(
    val isLoading: Boolean = true,
    val totalCrimes: Int = 0,
    val activePatrols: Int = 124, // Keep static for now since we don't have an endpoint for this
    val clearanceRate: Int = 84, // Keep static for now
    val districts: List<DistrictAnalytics> = emptyList(),
    val hotspots: List<HotspotAnalytics> = emptyList(),
    val error: String? = null
)

class OverviewViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(OverviewState())
    val uiState: StateFlow<OverviewState> = _uiState.asStateFlow()

    init {
        fetchData()
    }

    fun fetchData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            try {
                // Wait briefly for token if initialized at same time
                kotlinx.coroutines.delay(500)
                
                val districtsData = RetrofitClient.apiService.getDistricts()
                val hotspotsData = RetrofitClient.apiService.getHotspots()
                
                val totalCrimes = districtsData.sumOf { it.total }

                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    totalCrimes = totalCrimes,
                    districts = districtsData,
                    hotspots = hotspotsData
                )
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "An error occurred fetching data."
                )
            }
        }
    }
}
