#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <array>
#include <cmath>
#include <cstdint>
#include <deque>
#include <limits>
#include <optional>
#include <stdexcept>
#include <vector>

namespace py = pybind11;
struct Sample {
  double time;
  double value;
};
struct Stream {
  std::deque<Sample> buffer;
  double offset = 0, variance = 1,
         last = -std::numeric_limits<double>::infinity();
  bool calibrated = false;
  std::uint64_t late = 0, overflow = 0;
};
struct Frame {
  double time, estimate, variance, measurement;
  int active;
  bool initialized;
  std::vector<double> ages;
};
class Fusion {
  std::vector<Stream> streams;
  std::size_t capacity;
  double max_age, process_noise,
      last_tick = -std::numeric_limits<double>::infinity();
  double x = 0, p = 1;
  bool initialized = false;

public:
  Fusion(int count, std::size_t capacity_, double age, double noise)
      : streams(count > 0 && count <= 64
                    ? count
                    : throw std::invalid_argument("stream count")),
        capacity(capacity_), max_age(age), process_noise(noise) {
    if (capacity == 0 || capacity > 65536 || !std::isfinite(age) || age <= 0 ||
        !std::isfinite(noise) || noise <= 0)
      throw std::invalid_argument("configuration");
  }
  void calibrate(int id, double sensor, double reference, double variance) {
    auto &s = streams.at(id);
    if (s.calibrated || !std::isfinite(sensor) || !std::isfinite(reference) ||
        !std::isfinite(variance) || variance <= 0 || variance > 1e6)
      throw std::invalid_argument("calibration");
    s.offset = sensor - reference;
    s.variance = variance;
    s.calibrated = true;
  }
  bool ingest(int id, double sensor_time, double value) {
    auto &s = streams.at(id);
    if (!s.calibrated || !std::isfinite(sensor_time) || !std::isfinite(value) ||
        std::abs(value) > 1e9)
      throw std::invalid_argument("sample");
    double t = sensor_time - s.offset;
    if (t <= s.last || t <= last_tick) {
      ++s.late;
      return false;
    }
    s.last = t;
    if (s.buffer.size() == capacity) {
      s.buffer.pop_front();
      ++s.overflow;
    }
    s.buffer.push_back({t, value});
    return true;
  }
  Frame tick(double time) {
    if (!std::isfinite(time) || time <= last_tick)
      throw std::invalid_argument("tick order");
    double dt = std::isfinite(last_tick) ? time - last_tick : 0;
    last_tick = time;
    double weighted = 0, weights = 0;
    int active = 0;
    std::vector<double> ages;
    for (auto &s : streams) {
      while (s.buffer.size() > 1 && s.buffer[1].time <= time)
        s.buffer.pop_front();
      double age = -1;
      if (!s.buffer.empty() && s.buffer.front().time <= time) {
        age = time - s.buffer.front().time;
        if (age <= max_age) {
          // Age inflates uncertainty; stale sources cannot retain full weight.
          double w = 1.0 / (s.variance + process_noise * age);
          weighted += s.buffer.front().value * w;
          weights += w;
          ++active;
        }
      }
      ages.push_back(age);
    }
    p += process_noise * dt;
    double measurement = 0;
    if (active) {
      measurement = weighted / weights;
      double r = 1.0 / weights;
      if (!initialized) {
        x = measurement;
        p = r;
        initialized = true;
      } else {
        double gain = p / (p + r);
        x += gain * (measurement - x);
        p = (1 - gain) * p;
      }
    }
    return {time, x, p, measurement, active, initialized, ages};
  }
  py::list health() const {
    py::list result;
    for (const auto &s : streams) {
      py::dict row;
      row["buffered"] = s.buffer.size();
      row["late"] = s.late;
      row["overflow"] = s.overflow;
      row["offset"] = s.offset;
      result.append(row);
    }
    return result;
  }
};
PYBIND11_MODULE(_fusion, m) {
  py::class_<Frame>(m, "Frame")
      .def_readonly("time", &Frame::time)
      .def_readonly("estimate", &Frame::estimate)
      .def_readonly("variance", &Frame::variance)
      .def_readonly("measurement", &Frame::measurement)
      .def_readonly("active", &Frame::active)
      .def_readonly("initialized", &Frame::initialized)
      .def_readonly("ages", &Frame::ages);
  py::class_<Fusion>(m, "Fusion")
      .def(py::init<int, std::size_t, double, double>(), py::arg("count"),
           py::arg("capacity") = 128, py::arg("max_age") = 0.15,
           py::arg("process_noise") = 0.3)
      .def("calibrate", &Fusion::calibrate)
      .def("ingest", &Fusion::ingest)
      .def("tick", &Fusion::tick)
      .def("health", &Fusion::health);
}
