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

import com.example.crimerakshak.api.SQLQueryRequest

data class OverviewState(
    val isLoading: Boolean = true,
    val totalCrimes: Int = 0,
    val activePatrols: Int = 124,
    val clearanceRate: Int = 84,
    val districts: List<DistrictAnalytics> = emptyList(),
    val hotspots: List<HotspotAnalytics> = emptyList(),
    val pieChartData: List<Map<String, Any>> = emptyList(),
    val barChartData: List<Map<String, Any>> = emptyList(),
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
                kotlinx.coroutines.delay(500)
                
                val districtsData = RetrofitClient.apiService.getDistricts()
                val hotspotsData = RetrofitClient.apiService.getHotspots()
                
                // Fetch Pie Chart Data (Category Breakdown)
                val pieSql = """
                    SELECT 
                        SUM(theft) as theft, 
                        SUM(robbery) as robbery, 
                        SUM(burglary_day + burglary_night) as burglary, 
                        SUM(cyber_crime) as cyber_crime, 
                        SUM(murder) as murder 
                    FROM district_major_heads_yearly
                """.trimIndent()
                val pieResponse = RetrofitClient.apiService.runQuery(SQLQueryRequest(sql = pieSql))
                
                // Fetch Bar Chart Data (Monthly Comparison)
                val barSql = """
                    SELECT 
                        crime_head, 
                        january_2026 as current_month, 
                        december_2025 as prev_month, 
                        january_2025 as prev_year 
                    FROM crime_review_summary 
                    WHERE crime_head IN ('Theft', 'Economic Offences', 'Burglary', 'Cyber Crimes', 'Robbery', 'Murder') 
                    ORDER BY january_2026 DESC 
                    LIMIT 7
                """.trimIndent()
                val barResponse = RetrofitClient.apiService.runQuery(SQLQueryRequest(sql = barSql))
                
                val totalCrimes = districtsData.sumOf { it.total }

                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    totalCrimes = totalCrimes,
                    districts = districtsData,
                    hotspots = hotspotsData,
                    pieChartData = pieResponse.rows,
                    barChartData = barResponse.rows
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
