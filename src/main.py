#!/usr/bin/env python3
import threading
import time
import random
import queue
from Aloha.src.utils.budget_utls import cpu_load,memory_load


# ============================================================
#  Base Module Class
# ============================================================

class BaseModule(threading.Thread):
    def __init__(self, name, interval=1.0):
        super().__init__(daemon=True)
        self.name = name
        self.interval = interval
        self.running = False
        self.last_output = None

    def run(self):
        self.running = True
        print(f"[{self.name}] started")

        while self.running:
            start = time.time()

            # Simulate CPU + memory usage
            cpu_load(40)
            memory_load(256)

            # Module-specific work
            self.last_output = self.step()

            # Maintain interval
            elapsed = time.time() - start
            sleep_time = max(0.0, self.interval - elapsed)
            time.sleep(sleep_time)

        print(f"[{self.name}] stopped")

    def stop(self):
        self.running = False

    def step(self):
        """Override in subclass."""
        return None


# ============================================================
#  KrakenSDR Interface Module
# ============================================================

class KrakenSdrModule(BaseModule):
    def __init__(self, name, interval=0.2):
        super().__init__(name, interval)

    def step(self):
        # Dummy IQ samples (multi-channel)
        iq_data = {
            "channels": 5,
            "sample_rate": 2400000,
            "timestamp": time.time(),
            "iq": [random.random() for _ in range(1024)]  # placeholder
        }

        # Simulate SDR capture load
        cpu_load(50)
        memory_load(2048)

        print(f"[kraken] captured IQ block")
        return iq_data


# ============================================================
#  Radar DSP Module (beamforming + direction finding)
# ============================================================

class RadarDspModule(BaseModule):
    def __init__(self, name, interval=0.2):
        super().__init__(name, interval)
        self.iq_queue = queue.Queue(maxsize=10)

    def push_iq(self, iq):
        try:
            self.iq_queue.put_nowait(iq)
        except queue.Full:
            pass

    def step(self):
        if self.iq_queue.empty():
            return None

        iq = self.iq_queue.get()

        # Simulate DSP load (FFT, MUSIC, beamforming)
        cpu_load(120)
        memory_load(4096)

        # Dummy DOA estimate
        doa = {
            "azimuth_deg": random.uniform(0, 360),
            "elevation_deg": random.uniform(-10, 60),
            "snr": random.uniform(5, 40),
            "timestamp": time.time()
        }

        print(f"[dsp] DOA az={doa['azimuth_deg']:.1f}")
        return doa


# ============================================================
#  Radar Tracking Module (EKF placeholder)
# ============================================================

class RadarTrackingModule(BaseModule):
    def __init__(self, name, interval=0.5):
        super().__init__(name, interval)
        self.doa_queue = queue.Queue(maxsize=10)

    def push_doa(self, doa):
        try:
            self.doa_queue.put_nowait(doa)
        except queue.Full:
            pass

    def step(self):
        if self.doa_queue.empty():
            return None

        doa = self.doa_queue.get()

        # Simulate EKF tracking load
        cpu_load(80)
        memory_load(1024)

        # Dummy track estimate
        track = {
            "track_id": f"T{random.randint(1000,9999)}",
            "azimuth_deg": doa["azimuth_deg"] + random.uniform(-1, 1),
            "elevation_deg": doa["elevation_deg"] + random.uniform(-1, 1),
            "velocity": random.uniform(0, 50),
            "confidence": random.uniform(0.5, 0.99),
            "timestamp": time.time()
        }

        print(f"[tracking] track={track['track_id']}")
        return track


# ============================================================
#  TinyML Module (NPU inference)
# ============================================================

class TinyMlModule(BaseModule):
    def __init__(self, name, interval=0.5):
        super().__init__(name, interval)
        self.track_queue = queue.Queue(maxsize=10)

    def push_track(self, track):
        try:
            self.track_queue.put_nowait(track)
        except queue.Full:
            pass

    def step(self):
        if self.track_queue.empty():
            return None

        track = self.track_queue.get()

        # Simulate NPU inference load
        cpu_load(30)
        memory_load(512)

        # Dummy classification
        classified = {
            "track_id": track["track_id"],
            "label": random.choice(["aircraft", "drone", "bird", "unknown"]),
            "confidence": random.uniform(0.5, 0.99),
            "timestamp": time.time()
        }

        print(f"[tinyml] classified={classified['label']}")
        return classified


# ============================================================
#  Orchestrator
# ============================================================

class Orchestrator:
    def __init__(self):
        self.kraken = KrakenSdrModule("kraken", interval=0.2)
        self.dsp = RadarDspModule("dsp", interval=0.2)
        self.tracking = RadarTrackingModule("tracking", interval=0.5)
        self.tinyml = TinyMlModule("tinyml", interval=0.5)

        self.modules = [
            self.kraken,
            self.dsp,
            self.tracking,
            self.tinyml
        ]

    def start(self):
        print("[orchestrator] starting modules")
        for m in self.modules:
            m.start()

        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            # Kraken ? DSP
            if self.kraken.last_output:
                self.dsp.push_iq(self.kraken.last_output)

            # DSP ? Tracking
            if self.dsp.last_output:
                self.tracking.push_doa(self.dsp.last_output)

            # Tracking ? TinyML
            if self.tracking.last_output:
                self.tinyml.push_track(self.tracking.last_output)

            time.sleep(0.05)

    def stop(self):
        print("[orchestrator] stopping modules")
        for m in self.modules:
            m.stop()

        for m in self.modules:
            m.join()

    def run(self):
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[orchestrator] shutdown requested")
            self.stop()


# ============================================================
#  Main
# ============================================================

if __name__ == "__main__":
    orch = Orchestrator()
    orch.run()
