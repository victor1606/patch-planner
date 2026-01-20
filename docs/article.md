# PatchPlanner: A Simulation Framework for Evaluating Security Patch Deployment Strategies in Critical Infrastructure

**Abstract** — Security patch management in distributed critical infrastructure presents a fundamental trade-off between security (minimizing vulnerability exposure time) and availability (maintaining service uptime during updates). This paper presents PatchPlanner, a discrete-event simulation framework for modeling, planning, and evaluating patch deployment strategies. We implement seven deployment strategies ranging from naive Big Bang to adaptive Hybrid approaches, and evaluate them across three realistic infrastructure scenarios. Our experimental results demonstrate that constraint-aware strategies successfully maintain zero service-level downtime while achieving varying levels of security exposure reduction. Blue-Green deployment emerges as optimal for minimizing both exposure window and node unavailability, while Big Bang proves infeasible for any scenario with availability requirements. The framework provides infrastructure operators with quantitative metrics for strategy selection and validates the importance of availability-aware planning in dependable systems.

**Keywords** — patch management, deployment strategies, dependable systems, availability constraints, discrete-event simulation, critical infrastructure

---

## 1. Introduction

### 1.1 Context and Motivation

Modern software systems require frequent security updates to remediate discovered vulnerabilities. In critical infrastructures — data centers, industrial control systems, cloud platforms — this seemingly routine activity becomes a complex dependable systems engineering challenge.

The fundamental dilemma is as follows: on one hand, patches must be applied quickly to minimize the exposure window to attacks; on the other hand, the patching process frequently requires restarting services or rebooting systems, causing temporary unavailability. For critical systems with strict availability requirements (*high-availability*), this unavailability may be unacceptable.

The problem becomes even more complex when we consider:
- **Component dependencies**: A web service depends on an API, which depends on a database
- **Version compatibility**: Some components cannot function correctly if they are at different versions
- **Failure probability**: Patches can fail, requiring rollback or manual intervention
- **Availability constraints**: A minimum of *k* instances from each service must remain functional

### 1.2 Project Objectives

This project aims to develop a simulation framework that enables:

1. **Infrastructure modeling** as a dependency graph with availability constraints
2. **Implementation and comparison** of multiple deployment strategies
3. **Quantitative evaluation** of trade-offs between security and availability
4. **Generation of recommendations** for infrastructure operators

### 1.3 Contributions

The main contributions of this work are:

- A formal model for patch deployment planning as a constrained optimization problem
- Implementation of seven deployment strategies representing different points on the trade-off spectrum
- A discrete-event simulation engine for reproducible empirical evaluation
- Quantitative metrics that unify the security (exposure) and reliability (availability) domains
- Experimental results that validate guidelines for strategy selection in critical infrastructure

---

## 2. Related Work

### 2.1 Patch Management in Enterprise Systems

The specialized literature identifies patch management as one of the major challenges in operational security [1]. Studies show that delays in applying patches represent one of the main causes of security breaches, with an average of 60-150 days between a patch's publication and its application [2].

### 2.2 Deployment Strategies

**Rolling Deployment** is the standard technique for zero-downtime updates, applying changes incrementally on subsets of nodes [3]. **Blue-Green Deployment** maintains two identical environments, allowing instant switching between versions [4]. **Canary Deployment** tests changes on a small subset before complete rollout [5].

These strategies have been extensively studied in the context of application deployment, but less so in the specific context of security patches, where urgency and risk are critical factors.

### 2.3 Modeling and Simulation

Discrete-event simulation techniques are frequently used for evaluating distributed systems [6]. NetworkX and other graph libraries enable modeling dependencies between components [7].

### 2.4 Differentiation from Existing Work

Unlike previous works that focus on a single strategy or on application deployment, this project:
- Systematically compares seven different strategies
- Focuses specifically on security patches (with exposure metrics)
- Includes explicit availability constraints (*min_up*)
- Models version compatibility (DEGRADED, INCOMPATIBLE)

---

## 3. Article Contribution

### 3.1 System Architecture

PatchPlanner follows a four-stage architecture (Figure 1):

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    INPUT     │     │   PLANNING   │     │  SIMULATION  │     │    OUTPUT    │
│              │ --> │              │ --> │              │ --> │              │
│   Scenario   │     │   Strategy   │     │    Engine    │     │   Reports    │
│    (YAML)    │     │  Generator   │     │   Executor   │     │  & Metrics   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```
*Figure 1: PatchPlanner system pipeline architecture*

The **Input Component** parses YAML files that define the infrastructure, including nodes, dependencies, and constraints. The **Planning Component** generates a deployment plan using one of the seven implemented strategies. The **Simulation Component** executes the plan in a discrete-event simulator, injecting failures probabilistically and verifying constraints. The **Output Component** generates detailed reports with metrics.

### 3.2 Data Model

#### 3.2.1 Infrastructure Graph

The infrastructure is modeled as a directed graph $G = (V, E)$ where:
- $V$ = the set of nodes (hosts, services, databases)
- $E$ = the set of edges (dependencies between components)

Each node $v \in V$ has the following properties:
- **criticality** $\in \{1, 2, 3, 4, 5\}$: the criticality level
- **severity** $\in [0, 10]$: vulnerability severity (CVSS score)
- **patch_duration**: duration of patch application (seconds)
- **failure_probability** $\in [0, 1]$: probability of failure
- **min_up**: minimum number of healthy instances required

Each edge $e \in E$ has a compatibility level:
- **COMPATIBLE**: versions can safely differ
- **DEGRADED**: mixed versions cause performance degradation
- **INCOMPATIBLE**: components must be patched together

#### 3.2.2 Node States

A node can be in one of the following states:
- **HEALTHY**: operational, can process requests
- **DOWN**: temporarily unavailable (during patching)
- **FAILED**: failed, requires intervention

#### 3.2.3 Availability Constraint

For each service $s$ with $n_s$ instances and requirement $min\_up_s$, we define:

$$healthy_s(t) \geq min\_up_s, \quad \forall t$$

where $healthy_s(t)$ is the number of instances in the HEALTHY state at time $t$.

### 3.3 Deployment Strategies

We implemented seven strategies, each representing a different trade-off between speed, security, and availability.

#### 3.3.1 Big Bang

Applies the patch to all nodes simultaneously in a single step. It is the fastest strategy but invariably violates availability constraints.

#### 3.3.2 Rolling

Applies patches one by one for each service, respecting the constraint:

$$max\_down_s = n_s - min\_up_s$$

It never patches more than $max\_down_s$ nodes from a service simultaneously.

#### 3.3.3 Batch Rolling

Similar to Rolling, but groups nodes in batches of configurable size, accelerating the process.

#### 3.3.4 Blue-Green

Builds the new version in parallel (on additional capacity), then switches traffic instantly. Achieves zero node-level unavailability.

#### 3.3.5 Canary

Selects a small subset ("canary") from each service, applies the patch, waits for observation (60 seconds), then continues with the rest. Allows early detection of problems.

#### 3.3.6 Dependency-Aware Greedy

Respects the topological order of the dependency graph, patching dependencies before dependents. Minimizes time with mixed versions.

#### 3.3.7 Hybrid Risk-Aware

Adaptive strategy that calculates the risk of each group:

$$risk_v = severity_v \times criticality_v \times (1 + in\_degree_v + out\_degree_v)$$

For each group, it chooses Blue-Green if $min\_up \geq group\_size$, otherwise uses Rolling. Includes 30-second pauses as "guardrails" between groups.

### 3.4 Simulation Engine

The simulator implements a discrete-event model:

1. Processes plan steps sequentially
2. **Verifies constraints** before each patching step
3. Marks nodes as DOWN for the duration of patching
4. **Injects failures** probabilistically using seeded RNG (for reproducibility)
5. Performs rollback if failure occurs and is supported
6. Advances simulation clock
7. **Collects metrics** at each interval

### 3.5 Collected Metrics

#### 3.5.1 Timing Metrics
- **time_to_full_patch**: total duration until all nodes are patched
- **node_unavailability_seconds**: $\sum_{step} (|down\_nodes| \times duration)$

#### 3.5.2 Security Metrics
- **exposure_window_weighted**: 
$$\sum_{t} \sum_{v \in unpatched(t)} criticality_v \times severity_v \times \Delta t$$

#### 3.5.3 Compatibility Metrics
- **mixed_version_time_seconds**: time with edges in mixed version state
- **number_of_degraded_intervals**: intervals with active DEGRADED edges
- **number_of_incompatibility_violations**: violations of INCOMPATIBLE constraints

#### 3.5.4 Reliability Metrics
- **rollback_count**: number of rollbacks performed
- **total_downtime_seconds_overall**: time with $healthy_s < min\_up_s$

---

## 4. Results

### 4.1 Test Scenarios

We evaluated the strategies on three representative scenarios:

**Scenario 1 (HA Microservices)**: Multi-tier architecture with 13 nodes (2 hosts, 3 web, 3 API, 3 auth, 2 DB), varied min_up constraints (1-2), and DEGRADED edges between tiers.

**Scenario 2 (Compatibility Trap)**: 4 nodes with INCOMPATIBLE edges, testing the strategies' ability to handle atomic patches.

**Scenario 3 (Patch Risk)**: Critical host with high failure probability (20%), no rollback support, testing behavior under high-risk conditions.

### 4.2 Quantitative Results

#### Table 1: Scenario 1 Results (HA Microservices)

| Metric | Rolling | Batch | Canary | Blue-Green | DepGreedy | Hybrid |
|--------|---------|-------|--------|------------|-----------|--------|
| Time (s) | 315 | 630 | 375 | **120** | 960 | 1350 |
| Exposure | 90,150 | 162,255 | 106,920 | **47,160** | 202,440 | 247,455 |
| Node Unavail. (s) | 1,425 | 1,200 | 1,425 | **0** | 960 | **0** |
| Mixed Version (s) | 195 | 645 | 255 | **0** | 1,410 | 900 |
| Rollbacks | 1 | 3 | 1 | **0** | 2 | **0** |

*BigBang: FAILED (availability constraint violation)*

#### Table 2: Scenario 2 Results (Compatibility Trap)

| Metric | Rolling | Batch | Canary | Blue-Green | DepGreedy | Hybrid |
|--------|---------|-------|--------|------------|-----------|--------|
| Time (s) | 140 | 140 | 200 | **70** | 140 | 200 |
| Exposure | 13,965 | 13,965 | 17,955 | **9,310** | 13,965 | 21,485 |
| Incompat. Violations | 0 | 2 | 0 | 0 | 0 | 1 |

#### Table 3: Scenario 3 Results (Patch Risk)

| Metric | Rolling | Batch | Canary | Blue-Green | DepGreedy | Hybrid |
|--------|---------|-------|--------|------------|-----------|--------|
| Time (s) | 210 | 210 | 270 | **180** | 240 | 330 |
| Exposure | 15,030 | 15,030 | 17,010 | **14,040** | 16,020 | 17,010 |
| Node Unavail. (s) | 390 | 390 | 390 | **0** | 240 | 180 |
| Rollbacks | 1 | 1 | 1 | **0** | 1 | **0** |

### 4.3 Results Analysis

#### 4.3.1 Big Bang is Infeasible

In all three scenarios, the Big Bang strategy failed due to availability constraint violations. This confirms that a naive "patch all at once" approach is not viable for critical systems.

#### 4.3.2 Blue-Green is Optimal for Security and Availability

Blue-Green consistently achieved the best results:
- **Fastest** completion time (120s vs 315-1350s in Scenario 1)
- **Lowest exposure** to vulnerabilities (47,160 vs 90,150-247,455)
- **Zero unavailability** at node level
- **Zero rollbacks** (patches are applied on shadow capacity)
- **Zero mixed version time**

The trade-off is the need for additional capacity for the "green" environment.

#### 4.3.3 Rolling Provides Safety but Sacrifices Speed

Rolling represents the conservative compromise: moderate duration, but always maintains service availability. It is the recommended strategy when Blue-Green is not feasible.

#### 4.3.4 Hybrid Adds Overhead for Safety

The Hybrid strategy, while achieving zero rollbacks and zero unavailability when conditions allow Blue-Green, has the longest total duration due to "guardrail" pauses (1350s in Scenario 1). This overhead may be acceptable for systems where caution is paramount.

#### 4.3.5 Service-Level Downtime is Zero

All strategies that succeeded (6 out of 7) achieved **zero service-level downtime** (total_downtime_seconds_overall = 0). This validates the correctness of constraint-aware planning implementation.

### 4.4 Comparative Visualization

Figure 2 presents the visual comparison of strategies on key dimensions:

```
Completion Time (Scenario 1):
BlueGreen  ████████ 120s
Rolling    ███████████████████████████ 315s  
Canary     █████████████████████████████████ 375s
Batch      █████████████████████████████████████████████████████████ 630s
DepGreedy  ████████████████████████████████████████████████████████████████████████████████████████ 960s
Hybrid     █████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████ 1350s
```

```
Exposure Window (Scenario 1):
BlueGreen  ██████████ 47,160
Rolling    ██████████████████████████ 90,150
Canary     ██████████████████████████████ 106,920
Batch      █████████████████████████████████████████████████████ 162,255
DepGreedy  ██████████████████████████████████████████████████████████████████████████████████████████ 202,440
Hybrid     ████████████████████████████████████████████████████████████████████████████████████████████████████████████████ 247,455
```

---

## 5. Conclusions and Future Directions

### 5.1 Conclusions

This paper presented PatchPlanner, a simulation framework for evaluating security patch deployment strategies in critical infrastructure. The main conclusions are:

1. **Naive strategies (Big Bang) are infeasible** for systems with availability requirements. All tested scenarios rejected this approach.

2. **Blue-Green is optimal** when additional capacity is available, offering the best trade-off between speed, security, and availability.

3. **Rolling represents the safe fallback** when Blue-Green is not feasible, maintaining availability at moderate time cost.

4. **Constraint-aware planning** is essential: calculating $max\_down = n_s - min\_up_s$ per service before plan generation eliminates constraint violations at runtime.

5. **Quantitative metrics** enable objective comparisons and guide strategy selection based on operational priorities.

### 5.2 Future Directions

Future research directions include:

1. **Automatic optimization**: Applying search techniques (genetic algorithms, simulated annealing) to generate optimal plans given specific constraints.

2. **Dynamic scenarios**: Extension to model changes during execution (nodes failing independently of patching, urgent patch requests).

3. **Financial costs**: Integration of additional capacity costs to evaluate the economic trade-offs of Blue-Green.

4. **Validation on real systems**: Testing the framework on production infrastructure to validate model accuracy.

5. **Graphical interface**: Development of an interface for visualizing plans and simulations in real-time.

### 5.3 Exploitation of Results

The PatchPlanner framework can be used by:
- **Infrastructure operators** to evaluate and select patching strategies
- **Security teams** to quantify exposure risk based on the chosen strategy
- **System architects** to size the capacity needed for Blue-Green deployment
- **Researchers** to experiment with new strategies and metrics

The source code is available under an open-source license and can be extended with new strategies and scenarios.

---

## References

[1] A. Arora, R. Krishnan, A. Nandkumar, R. Telang, and Y. Yang, "Impact of Vulnerability Disclosure and Patch Availability - An Empirical Analysis," in *Third Workshop on the Economics of Information Security*, 2004.

[2] Ponemon Institute, "Costs and Consequences of Gaps in Vulnerability Response," *Ponemon Institute Research Report*, 2019.

[3] M. Fowler, "BlueGreenDeployment," martinfowler.com, 2010.

[4] D. Sato, "Canary Release," martinfowler.com, 2014.

[5] K. Morris, *Infrastructure as Code: Managing Servers in the Cloud*, O'Reilly Media, 2016.

[6] A. M. Law, *Simulation Modeling and Analysis*, 5th ed., McGraw-Hill, 2014.

[7] A. Hagberg, D. Schult, and P. Swart, "Exploring Network Structure, Dynamics, and Function using NetworkX," in *Proceedings of the 7th Python in Science Conference*, 2008.

[8] S. Newman, *Building Microservices: Designing Fine-Grained Systems*, O'Reilly Media, 2015.

---

## Appendix: Technology Stack

| Component | Technology | Role |
|-----------|------------|------|
| Core | Python 3.11+ | Implementation |
| Data Validation | Pydantic v2 | Data models |
| Graph Operations | NetworkX | Dependencies |
| Configuration | PyYAML | Scenario parsing |
| Visualization | Matplotlib | Charts |
| Testing | pytest | Unit tests |
