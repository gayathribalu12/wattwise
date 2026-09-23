# WATTWISE — Virtual Data Center Energy Autopilot

WATTWISE is a real-world experimental virtual data center built using multiple laptops as compute nodes. Instead of using simulated server metrics, WATTWISE runs actual containerized workloads and continuously monitors CPU, memory, GPU, temperature, network, disk I/O, workload status, and available power telemetry.

The system uses Docker for workload isolation and Kubernetes for multi-node orchestration. Prometheus collects infrastructure telemetry and Grafana provides real-time visualization. An ML layer will learn the relationship between workload characteristics, resource utilization, thermal conditions, and energy consumption. The optimization engine will then use these predictions to make workload-placement and scheduling decisions while considering energy, performance, and thermal constraints.

## Architecture

Workloads → Docker → Kubernetes → Compute Nodes
                                      ↓
                              Telemetry Collection
                                      ↓
                              Prometheus → Grafana
                                      ↓
                                  ML Engine
                                      ↓
                             Energy Prediction
                                      ↓
                              Optimization Engine
                                      ↓
                            Scheduling Decision

## Development Roadmap

- [ ] Local WSL2 environment
- [ ] Docker environment
- [ ] Real workload containers
- [ ] Prometheus monitoring
- [ ] Grafana dashboard
- [ ] Multi-laptop compute nodes
- [ ] Kubernetes cluster
- [ ] Energy/power telemetry
- [ ] Telemetry dataset
- [ ] ML energy prediction
- [ ] Workload demand prediction
- [ ] Multi-objective optimization
- [ ] Closed-loop workload scheduling

## Core Technologies

- Linux / WSL2
- Docker
- Kubernetes
- Prometheus
- Grafana
- Python
- FastAPI
- PostgreSQL
- PyTorch
- scikit-learn
- XGBoost
