# s360-radar-node Architecture
Sky360 Project - RADAR Node Specification

## 1. Overview

`s360-radar-node` is the **RF sensing and direction-finding node** in the Sky360 system.

Its purpose is to:

- Interface with **KrakenSDR** (5-channel coherent SDR)
- Acquire multi-channel IQ samples
- Perform **DSP processing** (FFT, MUSIC, beamforming, correlation)
- Estimate **Direction of Arrival (DOA)** (azimuth + elevation)
- Run **target tracking** (EKF-based)
- Run **TinyML inference** on the NPU for semantic classification
- Publish structured protobuf messages over **eCAL**
- Provide RF-based tracking to CORE, ASC, PTF, and NAS nodes

## 2. High-Level Architecture

```
s360-radar-node
 +-- orchestrator/
 |     +-- main orchestrator loop
 |     +-- module lifecycle mgmt
 |     +-- eCAL publishers/subscribers
 |     +-- IQ routing + DOA routing
 |
 +-- kraken/
 |     +-- KrakenSDR interface
 |     +-- multi-channel IQ acquisition
 |     +-- gain/frequency control
 |
 +-- dsp/
 |     +-- FFT + windowing
 |     +-- MUSIC / ESPRIT DOA estimation
 |     +-- beamforming + correlation
 |     +-- pb.sky.RadarDoa publisher
 |
 +-- tracking/
 |     +-- EKF-based RF target tracking
 |     +-- motion model + measurement model
 |     +-- pb.sky.RadarTrack publisher
 |
 +-- tinyml/
       +-- NPU inference (classification)
       +-- semantic labeling of RF tracks
       +-- pb.sky.RadarSemanticEvent publisher
```

## 3. Component Responsibilities

### **Orchestrator**
- Starts/stops modules
- Routes IQ samples - DSP - Tracking - TinyML
- Publishes heartbeat/status
- Manages eCAL publishers/subscribers
- Ensures deterministic DSP timing
- Handles backpressure (IQ block dropping, queue limits)

### **KrakenSDR Module**
- Interfaces with KrakenSDR hardware
- Configures gain, frequency, sample rate
- Acquires coherent multi-channel IQ blocks
- Provides timestamps for DSP alignment
- Publishes raw IQ blocks internally

### **DSP Module**
- Performs FFT + windowing
- Executes MUSIC/ESPRIT DOA estimation
- Computes azimuth/elevation + SNR
- Performs optional beamforming
- Publishes `RadarDoa` messages

### **Tracking Module**
- Runs EKF-based tracking
- Fuses DOA measurements over time
- Predicts future target positions
- Publishes `RadarTrack`
- Provides stable tracking even with noisy RF data

### **TinyML Module**
- Runs NPU inference on RF track features
- Classifies objects (aircraft, drone, bird, unknown)
- Publishes `RadarSemanticEvent`
- Provides confidence scores

# 4. Interfaces

Below are the formal interface definitions for **data flow**, **processing stages**, **inputs**, **outputs**, and **eCAL topics**.

## 4.1 DATA FLOW & ARCHITECTURE

| Component | Direction | Data Type | Topic | Description |
|----------|-----------|-----------|--------|-------------|
| KrakenSDR Module | Out | `RadarIqBlock` | `sky360/radar/iq` | Multi-channel IQ samples |
| DSP Module | Out | `RadarDoa` | `sky360/radar/doa` | DOA estimate (az/el/SNR) |
| Tracking Module | Out | `RadarTrack` | `sky360/radar/track` | EKF target state |
| TinyML Module | Out | `RadarSemanticEvent` | `sky360/radar/semantic` | Classified RF track |
| Orchestrator | Out | `RadarNodeStatus` | `sky360/radar/status` | Node health |
| Orchestrator | In | `TimingMessage` | `sky360/timing` | GNSS time alignment |

## 4.2 PROCESSING STAGES

| Stage | Process | Input | Output | Configurable | Notes |
|-------|---------|--------|---------|--------------|-------|
| IQ Acquisition | Multi-channel capture | KrakenSDR | IQ block | Gain, freq, rate | 5-channel coherent |
| DSP Preprocessing | FFT + window | IQ block | Spectrum | Window type | Hann/Hamming |
| DOA Estimation | MUSIC/ESPRIT | Spectrum | DOA | Antenna geometry | Requires calibration |
| Beamforming | Correlation | IQ block | Beamformed signal | Optional | Improves SNR |
| Tracking | EKF | DOA | RadarTrack | Motion model | Predictive tracking |
| TinyML | NPU inference | Track features | Semantic event | Model path | RK3588 NPU |

## 4.3 INPUT FIELDS (KrakenSDR - node)

### **RadarIqBlock Input Fields**

| Field Name | Proto Type | Required | Default | Range/Values | Description |
|------------|------------|----------|---------|--------------|-------------|
| channels | uint32 | Yes | 5 | 1..8 | Number of coherent channels |
| sample_rate | uint32 | Yes | - | Hz | SDR sample rate |
| iq | bytes | Yes | - | IQ samples | Interleaved complex samples |
| timestamp | Timestamp | Yes | - | GNSS time | SDR timestamp |

## 4.4 OUTPUT FIELDS (RADAR - other nodes)

### **Radar DOA Output**

| Field | Type | Description |
|-------|------|-------------|
| azimuth_deg | float | Estimated azimuth |
| elevation_deg | float | Estimated elevation |
| snr | float | Signal-to-noise ratio |
| timestamp | Timestamp | DOA time |

### **Radar Track Output (EKF)**

| Field | Type | Description |
|-------|------|-------------|
| track_id | string | Unique ID |
| azimuth_deg | float | Estimated azimuth |
| elevation_deg | float | Estimated elevation |
| velocity | float | Angular velocity |
| confidence | float | 0.0–1.0 |
| timestamp | Timestamp | Track time |

### **Radar Semantic Event Output (TinyML)**

| Field | Type | Description |
|-------|------|-------------|
| track_id | string | ID from EKF |
| label | string | aircraft/drone/bird/unknown |
| confidence | float | 0.0–1.0 |
| timestamp | Timestamp | Classification time |

# 5. eCAL TOPIC DEFINITIONS

| Topic Name | Direction | Message Type | Description |
|------------|-----------|--------------|-------------|
| `sky360/radar/iq` | Out | `RadarIqBlock` | Multi-channel IQ samples |
| `sky360/radar/doa` | Out | `RadarDoa` | DOA estimate |
| `sky360/radar/track` | Out | `RadarTrack` | EKF target state |
| `sky360/radar/semantic` | Out | `RadarSemanticEvent` | TinyML classification |
| `sky360/radar/status` | Out | `RadarNodeStatus` | Node health |
| `sky360/timing` | In | `TimingMessage` | GNSS time alignment |

