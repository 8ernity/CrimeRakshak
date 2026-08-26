// Bengaluru BBMP Wards GeoJSON and metadata
// Realistic ward boundaries covering Bengaluru metropolitan zones

export interface WardGeoJsonFeature {
  type: "Feature";
  properties: {
    ward_id: string;
    ward_name: string;
    district: string;
    risk_level: "high" | "medium" | "low";
    risk_score: number;
    lat: number;
    lng: number;
  };
  geometry: {
    type: "Polygon";
    coordinates: number[][][];
  };
}

export interface WardGeoJsonCollection {
  type: "FeatureCollection";
  name: string;
  comment: string;
  features: WardGeoJsonFeature[];
}

export const BENGALURU_WARDS_GEOJSON: WardGeoJsonCollection = {
  type: "FeatureCollection",
  name: "bengaluru_bbmp_wards",
  comment: "Metropolitan Bengaluru municipal ward zones",
  features: [
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W17",
        ward_name: "Jayanagar",
        district: "South",
        risk_level: "high",
        risk_score: 91,
        lat: 12.9250,
        lng: 77.5938,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.5800, 12.9380],
            [77.6080, 12.9380],
            [77.6080, 12.9120],
            [77.5800, 12.9120],
            [77.5800, 12.9380],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W04",
        ward_name: "Majestic",
        district: "Central",
        risk_level: "high",
        risk_score: 88,
        lat: 12.9767,
        lng: 77.5713,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.5620, 12.9860],
            [77.5850, 12.9860],
            [77.5850, 12.9700],
            [77.5620, 12.9700],
            [77.5620, 12.9860],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W22",
        ward_name: "KR Market",
        district: "Central",
        risk_level: "high",
        risk_score: 84,
        lat: 12.9634,
        lng: 77.5780,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.5650, 12.9700],
            [77.5880, 12.9700],
            [77.5880, 12.9550],
            [77.5650, 12.9550],
            [77.5650, 12.9700],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W11",
        ward_name: "Koramangala",
        district: "South",
        risk_level: "high",
        risk_score: 79,
        lat: 12.9352,
        lng: 77.6245,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.6100, 12.9480],
            [77.6420, 12.9480],
            [77.6420, 12.9200],
            [77.6100, 12.9200],
            [77.6100, 12.9480],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W08",
        ward_name: "Indiranagar",
        district: "East",
        risk_level: "medium",
        risk_score: 67,
        lat: 12.9784,
        lng: 77.6408,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.6250, 12.9900],
            [77.6580, 12.9900],
            [77.6580, 12.9650],
            [77.6250, 12.9650],
            [77.6250, 12.9900],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W31",
        ward_name: "Whitefield",
        district: "East",
        risk_level: "medium",
        risk_score: 72,
        lat: 12.9698,
        lng: 77.7500,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.7250, 12.9900],
            [77.7750, 12.9900],
            [77.7750, 12.9500],
            [77.7250, 12.9500],
            [77.7250, 12.9900],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W09",
        ward_name: "MG Road",
        district: "Central",
        risk_level: "medium",
        risk_score: 65,
        lat: 12.9747,
        lng: 77.6094,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.5980, 12.9820],
            [77.6250, 12.9820],
            [77.6250, 12.9650],
            [77.5980, 12.9650],
            [77.5980, 12.9820],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W10",
        ward_name: "Shivajinagar",
        district: "Central",
        risk_level: "medium",
        risk_score: 68,
        lat: 12.9866,
        lng: 77.5993,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.5900, 12.9980],
            [77.6150, 12.9980],
            [77.6150, 12.9800],
            [77.5900, 12.9800],
            [77.5900, 12.9980],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W55",
        ward_name: "HSR Layout",
        district: "South",
        risk_level: "medium",
        risk_score: 61,
        lat: 12.9116,
        lng: 77.6473,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.6320, 12.9220],
            [77.6650, 12.9220],
            [77.6650, 12.8980],
            [77.6320, 12.8980],
            [77.6320, 12.9220],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W02",
        ward_name: "Hebbal",
        district: "North",
        risk_level: "medium",
        risk_score: 63,
        lat: 13.0351,
        lng: 77.5985,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.5800, 13.0550],
            [77.6180, 13.0550],
            [77.6180, 13.0150],
            [77.5800, 13.0150],
            [77.5800, 13.0550],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W03",
        ward_name: "Rajajinagar",
        district: "West",
        risk_level: "medium",
        risk_score: 59,
        lat: 12.9942,
        lng: 77.5529,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.5350, 13.0100],
            [77.5680, 13.0100],
            [77.5680, 12.9800],
            [77.5350, 12.9800],
            [77.5350, 13.0100],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W45",
        ward_name: "Yelahanka",
        district: "North",
        risk_level: "low",
        risk_score: 42,
        lat: 13.1005,
        lng: 77.5963,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.5750, 13.1250],
            [77.6200, 13.1250],
            [77.6200, 13.0800],
            [77.5750, 13.0800],
            [77.5750, 13.1250],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W52",
        ward_name: "JP Nagar",
        district: "South",
        risk_level: "low",
        risk_score: 44,
        lat: 12.9063,
        lng: 77.5857,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.5700, 12.9150],
            [77.6000, 12.9150],
            [77.6000, 12.8900],
            [77.5700, 12.8900],
            [77.5700, 12.9150],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W60",
        ward_name: "Electronic City",
        district: "South",
        risk_level: "low",
        risk_score: 38,
        lat: 12.8451,
        lng: 77.6643,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.6450, 12.8600],
            [77.6850, 12.8600],
            [77.6850, 12.8250],
            [77.6450, 12.8250],
            [77.6450, 12.8600],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        ward_id: "BLR-W57",
        ward_name: "Bannerghatta",
        district: "South",
        risk_level: "low",
        risk_score: 36,
        lat: 12.8827,
        lng: 77.5977,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.5850, 12.8950],
            [77.6150, 12.8950],
            [77.6150, 12.8650],
            [77.5850, 12.8650],
            [77.5850, 12.8950],
          ],
        ],
      },
    },
  ],
};
