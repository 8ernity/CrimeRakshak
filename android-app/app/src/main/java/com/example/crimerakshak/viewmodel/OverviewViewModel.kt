package com.example.crimerakshak.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.crimerakshak.api.DistrictAnalytics
import com.example.crimerakshak.api.HotspotAnalytics
import com.example.crimerakshak.data.DatabaseHelper
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

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

class OverviewViewModel(application: Application) : AndroidViewModel(application) {
    private val _uiState = MutableStateFlow(OverviewState())
    val uiState: StateFlow<OverviewState> = _uiState.asStateFlow()

    private val dbHelper = DatabaseHelper(application)

    private val districtRanges = mapOf(
        "BENGALURU DIST" to "Central Range",
        "TUMAKURU" to "Central Range",
        "KOLAR" to "Central Range",
        "K.G.F" to "Central Range",
        "RAMANAGARA" to "Central Range",
        "CHIKKABALLAPURA" to "Central Range",
        "MYSURU DIST" to "Southern Range",
        "CHAMARAJANAGAR" to "Southern Range",
        "HASSAN" to "Southern Range",
        "KODAGU" to "Southern Range",
        "MANDYA" to "Southern Range",
        "SHIVAMOGGA" to "Eastern Range",
        "CHITRADURGA" to "Eastern Range",
        "DAVANAGERE" to "Eastern Range",
        "HAVERI" to "Eastern Range",
        "BELAGAVI DIST" to "Northern Range",
        "DHARWAD" to "Northern Range",
        "GADAG" to "Northern Range",
        "VIJAYAPURA" to "Northern Range",
        "BAGALKOT" to "Northern Range",
        "KALABURAGI" to "North Eastern Range",
        "BIDAR" to "North Eastern Range",
        "YADGIR" to "North Eastern Range",
        "RAICHUR" to "North Eastern Range",
        "KOPPAL" to "North Eastern Range",
        "BALLARI" to "North Eastern Range",
        "VIJAYANAGARA" to "North Eastern Range",
        "DAKSHINA KANNADA" to "Western Range",
        "UDUPI" to "Western Range",
        "UTTARA KANNADA" to "Western Range",
        "CHIKKAMAGALURU" to "Western Range",
        "BENGALURU CITY" to "Commissionerate",
        "MYSURU CITY" to "Commissionerate",
        "BELAGAVI CITY" to "Commissionerate",
        "HUBLI DHARWAD CITY" to "Commissionerate",
        "MANGALURU CITY" to "Commissionerate",
        "KALABURAGI CITY" to "Commissionerate",
        "RAILWAYS" to "Special Units",
        "CID" to "Special Units",
        "ISD" to "Special Units"
    )

    init {
        fetchData()
    }

    fun fetchData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            try {
                // Read from local SQLite
                
                val districtSql = """
                    SELECT 
                        district as name,
                        COALESCE(spl_local_laws, 0) as sll,
                        (
                            COALESCE(murder, 0) + COALESCE(dacoity, 0) + COALESCE(robbery, 0) + 
                            COALESCE(chain_snatching, 0) + COALESCE(burglary_day, 0) + COALESCE(burglary_night, 0) + 
                            COALESCE(theft, 0) + COALESCE(snatching, 0) + COALESCE(riots, 0) + 
                            COALESCE(cases_of_hurt, 0) + COALESCE(rape, 0) + COALESCE(dowry_deaths, 0) + 
                            COALESCE(pocso, 0) + COALESCE(sc_st_poa_act, 0) + COALESCE("107_crpc_126_bnss", 0) + 
                            COALESCE("109_crpc_128_bnss", 0) + COALESCE("110_crpc_129_bnss", 0) + COALESCE(cyber_crime, 0) + 
                            COALESCE(cr_br_of_trust, 0) + COALESCE(cheating, 0) + COALESCE(counterfeiting, 0) + 
                            COALESCE(kmmc, 0) + COALESCE(mmdr, 0) + COALESCE(motor_vehicles_theft, 0) + COALESCE(ndps, 0)
                        ) as ipc
                    FROM district_crime_matrix
                    WHERE district IS NOT NULL
                    ORDER BY (ipc + sll) DESC
                """.trimIndent()
                
                val hotspotSql = """
                    SELECT 
                        district,
                        COALESCE(murder, 0) as murder,
                        COALESCE(robbery, 0) as robbery,
                        COALESCE(theft, 0) as theft,
                        COALESCE(riots, 0) as riots,
                        COALESCE(cases_of_hurt, 0) as cases_of_hurt,
                        COALESCE(cyber_crime, 0) as cyber_crime
                    FROM district_crime_matrix
                    WHERE district IS NOT NULL
                """.trimIndent()
                
                val pieSql = """
                    SELECT 
                        SUM(theft) as theft, 
                        SUM(robbery) as robbery, 
                        SUM(burglary_day + burglary_night) as burglary, 
                        SUM(cyber_crime) as cyber_crime, 
                        SUM(murder) as murder 
                    FROM district_major_heads_yearly
                """.trimIndent()
                
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

                val districtRows = dbHelper.runQuery(districtSql)
                val districtsData = districtRows.map { row ->
                    val name = row["name"].toString()
                    val ipc = (row["ipc"] as? Number)?.toInt() ?: 0
                    val sll = (row["sll"] as? Number)?.toInt() ?: 0
                    DistrictAnalytics(
                        name = name,
                        range = districtRanges[name] ?: "Other",
                        ipc = ipc,
                        sll = sll,
                        total = ipc + sll
                    )
                }
                
                val hotspotRows = dbHelper.runQuery(hotspotSql)
                val hotspotsData = hotspotRows.map { row ->
                    val district = row["district"].toString()
                    val murder = (row["murder"] as? Number)?.toInt() ?: 0
                    val robbery = (row["robbery"] as? Number)?.toInt() ?: 0
                    val theft = (row["theft"] as? Number)?.toInt() ?: 0
                    val riots = (row["riots"] as? Number)?.toInt() ?: 0
                    val casesOfHurt = (row["cases_of_hurt"] as? Number)?.toInt() ?: 0
                    val cyberCrime = (row["cyber_crime"] as? Number)?.toInt() ?: 0
                    HotspotAnalytics(
                        district = district,
                        total = murder + robbery + theft + riots + casesOfHurt + cyberCrime,
                        murder = murder,
                        robbery = robbery,
                        theft = theft,
                        riots = riots,
                        casesOfHurt = casesOfHurt,
                        cyberCrime = cyberCrime
                    )
                }
                
                val pieChartData = dbHelper.runQuery(pieSql)
                val barChartData = dbHelper.runQuery(barSql)
                
                val totalCrimes = districtsData.sumOf { it.total }

                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    totalCrimes = totalCrimes,
                    districts = districtsData,
                    hotspots = hotspotsData,
                    pieChartData = pieChartData,
                    barChartData = barChartData
                )
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "An error occurred fetching data from local database."
                )
            }
        }
    }
}
