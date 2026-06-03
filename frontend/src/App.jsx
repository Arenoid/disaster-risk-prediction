import { useState, useEffect } from "react";
import { MapContainer, TileLayer, GeoJSON} from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './App.css'

const RISK_COLOR = {
  high: "#f00505",
  medium: "#fcf06a",
  low: "#72fc72",
}

function getRiskColor(risk){
  return RISK_COLOR[risk] || '#ccc'
}

export default function App(){
  const [districts, setDistricts] = useState([])
  const [geojson, setGeojson] = useState(null)
  const [selected, setSelected] = useState(null)
  const [riskType, setRiskType] = useState('flood')
  const [loading, setLoading] = useState(true)


  useEffect(() =>{
    fetch("https://disaster-risk-prediction-4s7v.onrender.com/districts")
      .then(r => r.json())
      .then(data => {
        setDistricts(data)
        setLoading(false)
      })
  }, [])

  useEffect(()=>{
    fetch('/nepal_districts.geojson')
    .then(r=>r.json())
    .then(setGeojson)
  }, [])

  const riskMap = {}
  districts.forEach(d=>{
    riskMap[d.adm2_name] = {
      flood: d.flood_risk_pred,
      landslide: d.landslide_risk_pred,
      eq:d.eq_risk,
      ...d
    }
  })

  const riskKey = riskType === 'earthquake' ? 'eq': riskType
  function styleFeature(feature){
    const name = feature.properties.adm2_name || feature.properties.ADM2_EN
    const data = riskMap[name]
    return {
      fillColor: data? getRiskColor(data[riskKey]): '#ccc',
      fillOpacity:0.75,
      color: '#fff',
      weight: 1,
    }
  }



  function onEachFeature(feature,layer){
    const name = feature.properties.adm2_name || feature.properties.ADM2_EN
    layer.on({
      click:() =>{
        console.log('clicked:',name,riskMap[name])
        setSelected(riskMap[name] || null)
      },
      click: () => setSelected(riskMap[name] || null),
      mouseover:(e) =>e.target.setStyle({fillOpacity: 0.95, weight:2 }),
      mouseout: (e) =>e.target.setStyle({fillOpacity:0.75, weight:1}),
    })
  }

  if(loading) return <div className="loading">Loading...</div>

  return(
    <div className= "App">
        <header className="header">
          <div className="header-left">
            <h1>Nepal Disaster Risk Prediction Model</h1>
            <span className = "subtitle">For all 77 Districts of Nepal</span>
    </div>
    <div className="toggle-group">
          {['flood', 'landslide', 'earthquake'].map(t=>(
            <button key={t}
            className={`toggle-btn ${riskType === t ? 'active':''}`}
            onClick= {() => setRiskType(t)}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
          ))}    
    </div>
    </header>
  
  <div className="main">
    <div className="map-wrap">
          <MapContainer center={[28.3949, 84.124]} zoom = {7} className="map">
            <TileLayer
            url = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
            attribution=" = '&copy; CartoDB"
          />
          {geojson &&(
            <GeoJSON
            key={riskType}
            data={geojson}
            style = {styleFeature}
            onEachFeature = {onEachFeature}/>
          )}
            </MapContainer>

   <div className="legend">
          {Object.entries(RISK_COLOR).map(([level, color]) => (
              <div key={level} className="legend-item">
                <span className="legend-dot" style = {{background:color}}/>
                {level.charAt(0).toUpperCase()+level.slice(1)}
                </div>
          ))}
    </div>
    </div>       

  <div className = "sidebar">
    {selected ? (
      <>
      <h2>{selected.adm2_name}</h2>
      <div className="risk-cards">
        <RiskCard label = "Flood" value = {selected.flood_risk_pred}/>
        <RiskCard label = "Landslide" value = {selected.landslide_risk_pred}/>
        <RiskCard label = "Earthquake" value = {selected.eq_risk}/>
      </div>

      <div className="stats">
        <Stat label = "No of Flood" value = {selected.flood_count}/>
        <Stat label = "No of Landslides" value = {selected.landslide_count}/>
        <Stat label = "Earthquakes" value = {selected.eq_count}/>
        <Stat label = "Maximum magnitude of Earthquake" value = {selected.eq_max_mag}/>
        <Stat label = "Average Magnitude of Earthquake" value = {selected.eq_avg_mag?.toFixed(2)}/>
        <Stat label = "Area of District" value = {`${Math.round(selected.area_sqkm)}km²`}/>
      </div>
      </>
    ) : (
      <div className="placeholder">
        <p>Click a district to view the risk of Flood/Earthquake/Landslide</p>
      </div>
    )}
    </div>
  </div>
  </div>
  )
}

function RiskCard({label, value}){
  return (
    <div className= "risk-card" style = {{borderColor: getRiskColor(value)}}>
      <span className="risk-label">{label}</span>
      <span className = "risk-value" style = {{color: getRiskColor(value)}}>
        {value ? value.charAt(0).toUpperCase()+value.slice(1) : '-'}
      </span>
    </div>
  )
}

function Stat({label, value}){
  return(
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span className ="stat-value">{value ?? '-'}</span>
    </div>
  )
}
