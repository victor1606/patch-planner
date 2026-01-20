# PatchPlanner Presentation
<!-- Use with Marp, reveal.js, or as reference for PowerPoint/Google Slides -->

---

## Slide 1: Title

# PatchPlanner
### A Simulation Framework for Evaluating Security Patch Deployment Strategies in Critical Infrastructure

**Author:** [Your Name]  
**Date:** January 2026

### 📝 Speaker Notes (Slide 1)

> Good morning/afternoon everyone. Today I'm going to present PatchPlanner, a simulation framework I developed to address one of the most challenging problems in operational security: how do we apply security patches to critical systems without breaking them?
>
> This project sits at the intersection of two traditionally separate domains: cybersecurity, which tells us "patch fast or get hacked," and systems reliability, which tells us "don't touch anything that's working." PatchPlanner provides a way to quantitatively evaluate different strategies for resolving this tension.
>
> By the end of this presentation, you'll understand why naive patching approaches fail, which strategies work best under different conditions, and how our simulation framework can help infrastructure operators make data-driven decisions.

---

## Slide 2: The Problem

### Security vs. Availability Trade-off

**The Dilemma:**
- 🔒 Patches must be applied **quickly** → minimize vulnerability exposure
- ⚡ Patching causes **downtime** → services restart, systems reboot
- 🏭 Critical infrastructure has **strict availability requirements**

**Complexity Factors:**
- Component dependencies (web → API → database)
- Version compatibility between components
- Patch failure probability
- Minimum instances that must stay running (*min_up*)

> 📊 Average patch delay: **60-150 days** between publication and application

### 📝 Speaker Notes (Slide 2)

> Let me set the stage with the core problem we're solving.
>
> **The Fundamental Trade-off:** When a security vulnerability is discovered and a patch is released, there's immediate pressure to apply it. Every hour you wait, attackers could be exploiting that vulnerability. Industry research shows that the average time between a patch being published and actually being applied is 60 to 150 days—that's two to five months of exposure!
>
> But here's the catch: applying a patch isn't free. It typically requires restarting the service, and sometimes even rebooting the entire server. During that time, the system is unavailable. For a personal laptop, that's a minor inconvenience. For a hospital's patient management system, a bank's transaction processor, or a power grid's control system—that downtime could be catastrophic.
>
> **What makes this even harder?** Four key complexity factors:
>
> 1. **Dependencies:** Modern systems are interconnected. Your web frontend talks to an API, which talks to an authentication service, which talks to a database. You can't just patch things randomly—if you update the API before the web frontend is ready for the new version, things break.
>
> 2. **Version Compatibility:** Some components can tolerate version differences gracefully, others experience degraded performance, and some are completely incompatible with mixed versions. You need to know which is which.
>
> 3. **Failure Probability:** Patches can fail. Maybe 5% of the time, maybe 20%. When a patch fails, you might need to rollback, which takes more time and leaves you exposed even longer.
>
> 4. **Minimum Availability (min_up):** Critical services typically run multiple instances—say, 3 copies of your API server behind a load balancer. The constraint might be "at least 2 must always be running." This limits how many you can patch simultaneously.
>
> So the question becomes: **How do you navigate all these constraints while minimizing both security risk and downtime?** That's exactly what PatchPlanner helps answer.

---

## Slide 3: Project Objectives

### What We Built

1. **Infrastructure Modeling**
   - Dependency graph with availability constraints

2. **Strategy Comparison**
   - 7 deployment strategies implemented

3. **Quantitative Evaluation**
   - Trade-off metrics between security and availability

4. **Decision Support**
   - Recommendations for infrastructure operators

### 📝 Speaker Notes (Slide 3)

> Given this problem, let me explain what we set out to build and the four main objectives of this project.
>
> **Objective 1 - Infrastructure Modeling:** First, we needed a way to represent real infrastructure in a format that a computer can reason about. We model the infrastructure as a directed graph—nodes are your servers, services, and databases; edges are the dependencies between them. Each node carries properties like how critical it is, how severe its current vulnerability is, how long patching takes, and how likely the patch is to fail. We also capture the minimum number of healthy instances required per service—the "min_up" constraint.
>
> **Objective 2 - Strategy Comparison:** We didn't want to just implement one patching approach—we wanted to systematically compare different strategies. We implemented seven strategies, ranging from the naive "patch everything at once" approach to sophisticated adaptive strategies that consider risk factors. Each strategy represents a different point on the trade-off spectrum between speed and safety.
>
> **Objective 3 - Quantitative Evaluation:** The key innovation here is that we don't just say "this strategy is better"—we provide hard numbers. How many seconds were nodes unavailable? What was the total exposure to vulnerabilities? How many rollbacks were needed? These metrics allow objective comparison rather than subjective judgment.
>
> **Objective 4 - Decision Support:** Ultimately, this is a practical tool. The framework generates recommendations: "For your infrastructure profile, use Blue-Green if you have spare capacity, otherwise use Rolling." It helps operators make informed decisions rather than guessing.

---

## Slide 4: System Architecture

### Four-Stage Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    INPUT     │     │   PLANNING   │     │  SIMULATION  │     │    OUTPUT    │
│              │ --> │              │ --> │              │ --> │              │
│   Scenario   │     │   Strategy   │     │    Engine    │     │   Reports    │
│    (YAML)    │     │  Generator   │     │   Executor   │     │  & Metrics   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

**Technologies:** Python 3.11+ | Pydantic | NetworkX | PyYAML | Matplotlib | pytest

### 📝 Speaker Notes (Slide 4)

> Now let me walk you through how PatchPlanner actually works. It's organized as a four-stage pipeline.
>
> **Stage 1 - Input:** Everything starts with a YAML configuration file that describes your infrastructure. This is human-readable and easy to write. You define your nodes—maybe "web-1", "web-2", "api-1", "database-primary"—their properties, and how they depend on each other. You also specify constraints like "the web service needs at least 2 of 3 instances running at all times."
>
> **Stage 2 - Planning:** Once the infrastructure is loaded, we feed it into a strategy generator. You choose which strategy you want to evaluate—say, Rolling or Blue-Green—and the planner generates a detailed deployment plan. This plan specifies exactly which nodes to patch in which order, with which timing. The planner is constraint-aware, meaning it calculates upfront how many nodes from each service can be patched simultaneously without violating availability requirements.
>
> **Stage 3 - Simulation:** This is the heart of the system. We built a discrete-event simulator that executes the plan step by step. It advances a virtual clock, marks nodes as "down" when they're being patched, probabilistically injects failures using a seeded random number generator for reproducibility, performs rollbacks when failures occur, and continuously checks that availability constraints are satisfied. Think of it as a "dry run" of your patching process—you find problems in simulation rather than in production.
>
> **Stage 4 - Output:** Finally, we generate detailed reports and metrics. These include timing metrics (how long did it take?), security metrics (what was the total exposure?), compatibility metrics (how long were we running mixed versions?), and reliability metrics (how many failures and rollbacks?).
>
> **Technology stack:** The implementation uses Python 3.11, Pydantic for data validation (ensuring our models are correct), NetworkX for graph operations (calculating dependencies, topological sorting), PyYAML for configuration parsing, Matplotlib for visualization, and pytest for testing. The codebase has comprehensive test coverage to ensure correctness.

---

## Slide 5: Data Model

### Infrastructure as a Graph

**Graph G = (V, E)**
- **Nodes (V):** Hosts, services, databases
- **Edges (E):** Dependencies between components

**Node Properties:**
| Property | Description |
|----------|-------------|
| criticality | Level 1-5 |
| severity | CVSS score (0-10) |
| patch_duration | Time to apply patch |
| failure_probability | Chance of failure |
| min_up | Minimum healthy instances |

**Edge Compatibility:** COMPATIBLE | DEGRADED | INCOMPATIBLE

### 📝 Speaker Notes (Slide 5)

> Let me dive deeper into how we model the infrastructure, because this is the foundation of everything else.
>
> **The Graph Model:** We represent infrastructure as a directed graph G with vertices V and edges E. Each vertex is a component—could be a physical host, a microservice, a database instance, or any patchable entity. Each directed edge represents a dependency: if there's an edge from A to B, it means A depends on B. For example, your web frontend depends on your API, and your API depends on your database.
>
> **Node Properties - Let me explain each one:**
>
> - **Criticality (1-5):** How important is this component? A criticality of 5 means "if this breaks, the business stops." A criticality of 1 means "we can live without it temporarily." This affects how we prioritize and how we calculate risk.
>
> - **Severity (0-10):** This is the CVSS score of the vulnerability being patched. CVSS is the industry standard for rating vulnerabilities—10 is critical (like remote code execution with no authentication), while 2-3 might be a minor information disclosure. Higher severity means higher urgency to patch.
>
> - **Patch Duration:** How long does it take to apply the patch? This could be 30 seconds for a simple service restart or 5 minutes for a full system reboot with verification. This directly impacts how long nodes are unavailable.
>
> - **Failure Probability:** What's the chance the patch fails? In our scenarios, this ranges from 5% (typical) to 20% (high-risk patches). Failed patches require rollback, adding time and complexity.
>
> - **Min_up:** The minimum number of instances that must remain healthy. If you have 3 web servers and min_up is 2, you can only patch 1 at a time. This is the core availability constraint.
>
> **Edge Compatibility - Three levels:**
>
> - **COMPATIBLE:** The connected components can safely run at different versions. No problem having web-v2 talk to api-v1.
>
> - **DEGRADED:** Mixed versions work, but with reduced performance or functionality. Maybe some new features don't work, or there's extra latency. We track how long the system spends in this state.
>
> - **INCOMPATIBLE:** These components MUST be patched together. If you patch one without the other, the system breaks. This is common with tightly coupled components that share protocols or data formats.
>
> This model captures the essential complexity of real infrastructure while remaining tractable for simulation and analysis.

---

## Slide 6: Deployment Strategies (1/2)

### Seven Strategies Implemented

| Strategy | Description | Trade-off |
|----------|-------------|-----------|
| **Big Bang** | All nodes at once | ⚡ Fast, ❌ Breaks availability |
| **Rolling** | One by one per service | ✅ Safe, 🐢 Slow |
| **Batch Rolling** | Groups of nodes | ⚖️ Balanced |
| **Blue-Green** | Parallel environment, instant switch | ✅ Zero downtime, 💰 Extra capacity |

### 📝 Speaker Notes (Slide 6)

> Now let's look at the seven deployment strategies we implemented. I'll cover the first four here and the remaining three on the next slide.
>
> **Strategy 1 - Big Bang:**
> This is the naive approach: patch everything at once, in a single step. It's theoretically the fastest—if you have 10 nodes that each take 30 seconds to patch, you're done in 30 seconds total because they're all patched in parallel.
>
> The problem? Every node goes down simultaneously. If your min_up constraint says "at least 2 of 3 web servers must be running," and you take all 3 down at once, you've violated the constraint immediately. **In our experiments, Big Bang failed in EVERY scenario that had any availability requirements.** It's only viable for systems where complete downtime is acceptable—which is almost never the case for critical infrastructure.
>
> **Strategy 2 - Rolling:**
> This is the industry standard for zero-downtime deployments. The idea is simple: patch one node at a time within each service group, wait for it to come back up, then move to the next.
>
> The key calculation is: max_down = total_instances - min_up. If you have 3 web servers and min_up is 2, then max_down is 1—you can only have 1 node down at any time. Rolling respects this constraint by never exceeding max_down simultaneous patches per service.
>
> The trade-off is speed. If you have 10 nodes and can only patch 1 at a time, and each takes 30 seconds, you're looking at 5 minutes total instead of 30 seconds. But you maintain availability throughout.
>
> **Strategy 3 - Batch Rolling:**
> This is an optimization of Rolling. Instead of patching one node at a time, we patch in batches. If max_down is 3, we patch 3 nodes simultaneously, wait for them all to complete, then patch the next 3.
>
> This is faster than pure Rolling but still respects constraints. It's a balanced approach when you want some speed improvement without going to the complexity of Blue-Green.
>
> **Strategy 4 - Blue-Green:**
> This is the gold standard for zero-downtime deployments. The concept: you maintain two identical environments, "blue" (current) and "green" (new). You apply patches to the green environment while blue continues serving traffic. Once green is fully patched and verified, you switch traffic from blue to green instantly.
>
> The result is zero node unavailability from the user's perspective—there's always a healthy environment serving requests. The patches are applied on shadow capacity, and the switchover is instantaneous.
>
> The trade-off is cost: you need double the infrastructure capacity to run both environments. For a company with 100 servers, that means having 200 servers (or the cloud capacity for it) during patching. For some organizations, this cost is worth the reliability; for others, it's prohibitive.

---

## Slide 7: Deployment Strategies (2/2)

### Seven Strategies (continued)

| Strategy | Description | Trade-off |
|----------|-------------|-----------|
| **Canary** | Small subset first, observe, then continue | 🔍 Early problem detection |
| **Dep-Greedy** | Topological order (deps first) | 📊 Minimizes mixed versions |
| **Hybrid** | Risk-aware, adaptive selection | 🧠 Smart but slower |

**Hybrid Risk Formula:**
$$risk_v = severity \times criticality \times (1 + in\_degree + out\_degree)$$

### 📝 Speaker Notes (Slide 7)

> Let me continue with the remaining three strategies, which are more sophisticated.
>
> **Strategy 5 - Canary:**
> The Canary strategy is named after the "canary in the coal mine" concept. Before rolling out a patch to all nodes, you first apply it to a small subset—the "canaries." Then you wait and observe. In our implementation, we wait 60 seconds after patching the canaries before proceeding.
>
> Why? Because some problems don't manifest immediately. A patch might apply successfully, the service might start correctly, but then crash after 30 seconds due to a memory leak or configuration issue. By waiting and observing the canaries, you catch these delayed failures before they affect your entire fleet.
>
> If the canaries survive the observation period, you proceed with patching the rest of the nodes using a Rolling approach. If a canary fails, you can stop and investigate before causing widespread damage.
>
> The trade-off is time: that 60-second observation period adds up, especially if you have many services. But for risk-averse organizations, this early warning system is invaluable.
>
> **Strategy 6 - Dependency-Aware Greedy (Dep-Greedy):**
> This strategy considers the dependency graph structure. The idea is: patch dependencies before dependents. Using topological sorting, we identify which components are "leaves" (no dependencies) and which are "roots" (many things depend on them).
>
> We patch from the bottom up: databases first, then the APIs that depend on them, then the web frontends that depend on the APIs. This approach minimizes the time the system spends with mixed versions—where some components are on the new version and others are on the old version.
>
> Why does mixed version time matter? Because DEGRADED compatibility edges cause performance problems. The less time you spend with version mismatches, the less impact users experience.
>
> **Strategy 7 - Hybrid Risk-Aware:**
> This is our most sophisticated strategy. It doesn't use a fixed approach—instead, it adapts based on risk assessment.
>
> First, it calculates a risk score for each node using the formula shown: severity times criticality times a connectivity factor. Highly connected nodes (many dependencies going in and out) are riskier because their failure affects more components.
>
> Then, for each group of nodes to be patched, the Hybrid strategy asks: "Can we use Blue-Green here?" If there's enough spare capacity (min_up allows it), it uses Blue-Green for zero downtime. If not, it falls back to Rolling.
>
> It also adds 30-second "guardrail" pauses between groups. These pauses are checkpoints where operators could intervene if something looks wrong.
>
> The trade-off is complexity and time. The Hybrid strategy takes the longest in our experiments—but it achieves zero rollbacks and zero unavailability when conditions allow. For extremely critical systems where every precaution is warranted, this overhead may be acceptable.

---

## Slide 8: Test Scenarios & Results

### Three Evaluation Scenarios

| Scenario | Description | Nodes |
|----------|-------------|-------|
| **HA Microservices** | Multi-tier architecture | 13 nodes |
| **Compatibility Trap** | INCOMPATIBLE edges | 4 nodes |
| **Patch Risk** | 20% failure probability | 3 nodes |

### Key Results (Scenario 1)

| Strategy | Time | Exposure | Node Unavail. | Rollbacks |
|----------|------|----------|---------------|-----------|
| **Blue-Green** | **120s** | **47,160** | **0** | **0** |
| Rolling | 315s | 90,150 | 1,425 | 1 |
| Hybrid | 1,350s | 247,455 | 0 | 0 |
| Big Bang | ❌ FAILED | - | - | - |

### 📝 Speaker Notes (Slide 8)

> Now let's look at how we tested these strategies and what the results tell us. We designed three scenarios that stress-test different aspects of the strategies.
>
> **Scenario 1 - High-Availability Microservices:**
> This is a realistic multi-tier architecture with 13 nodes: 2 physical hosts, 3 web servers, 3 API servers, 3 authentication services, and 2 database instances. Each service has min_up constraints—web needs 2 of 3, API needs 2 of 3, etc. The edges between tiers are marked as DEGRADED, meaning mixed versions cause performance degradation but don't break functionality.
>
> This scenario tests the strategies' ability to maintain service availability while navigating complex dependencies.
>
> **Scenario 2 - Compatibility Trap:**
> This is a smaller scenario with just 4 nodes, but the edges are marked INCOMPATIBLE. This means components absolutely cannot run at different versions—they must be patched atomically.
>
> This scenario exposes strategies that don't properly handle compatibility constraints. Some strategies that work fine in Scenario 1 will cause incompatibility violations here.
>
> **Scenario 3 - Patch Risk:**
> This scenario has a critical host with a 20% failure probability and no rollback support. When the patch fails, you're stuck—you can't automatically recover.
>
> This tests strategies' resilience to failures and their ability to handle high-risk components appropriately.
>
> **Interpreting the Results Table:**
>
> Let me walk through the Scenario 1 numbers:
>
> - **Time:** Blue-Green completed in just 120 seconds—that's 2 minutes. Rolling took 315 seconds (over 5 minutes), and Hybrid took 1,350 seconds (22.5 minutes!). The Hybrid overhead comes from those guardrail pauses and risk calculations.
>
> - **Exposure:** This is the weighted vulnerability exposure—lower is better. It combines how long nodes were unpatched with how critical and severe their vulnerabilities were. Blue-Green's 47,160 is less than half of Rolling's 90,150. Why? Because Blue-Green finishes faster, so nodes spend less time unpatched.
>
> - **Node Unavailability:** This measures node-seconds of downtime. Blue-Green achieves zero because patches are applied to shadow capacity. Rolling has 1,425 node-seconds—that's the cumulative time nodes spent in the DOWN state during patching.
>
> - **Rollbacks:** Blue-Green has zero rollbacks because if a patch fails on the green environment, you simply don't switch over—the blue environment keeps running untouched. Rolling had 1 rollback when a patch failed and had to be reverted.
>
> - **Big Bang FAILED:** This is critical—Big Bang didn't even complete. It was rejected immediately because patching all nodes simultaneously would violate the min_up constraints.

---

## Slide 9: Key Findings

### What We Learned

1. ❌ **Big Bang is Infeasible**
   - Failed in ALL scenarios with availability requirements

2. 🏆 **Blue-Green is Optimal**
   - Fastest completion, lowest exposure, zero downtime
   - Trade-off: requires additional infrastructure capacity

3. ✅ **Rolling is the Safe Fallback**
   - When Blue-Green not feasible, maintains availability

4. 🎯 **Constraint-Aware Planning Works**
   - All successful strategies achieved **zero service-level downtime**

5. 📊 **Quantitative Metrics Enable Objective Comparison**
   - No more guessing—data-driven strategy selection

### 📝 Speaker Notes (Slide 9)

> Let me synthesize our experimental findings into five key takeaways.
>
> **Finding 1 - Big Bang is Infeasible:**
> This might seem obvious, but it's important to state definitively: the naive approach of "just patch everything at once" is not viable for any system with availability requirements. In all three of our scenarios, Big Bang failed. It couldn't even produce a valid plan.
>
> Why does this matter? Because in the real world, under time pressure, there's always temptation to "just do it quickly." Our results provide concrete evidence that this approach will fail. You cannot shortcut the problem.
>
> **Finding 2 - Blue-Green is Optimal:**
> Across all metrics, Blue-Green consistently outperformed other strategies. It was fastest (120s vs 315-1350s in Scenario 1), had the lowest exposure (47,160 vs 90,150-247,455), zero node unavailability, zero rollbacks, and zero mixed version time.
>
> This makes intuitive sense: by using parallel capacity, you avoid all the constraints that slow other strategies down. You're not waiting for nodes to come back up, you're not limited by how many you can patch simultaneously.
>
> The trade-off is real though: you need that extra capacity. For cloud-native organizations, this might mean temporarily spinning up additional instances—feasible but has cost implications. For on-premises infrastructure, you need to have that hardware available. The framework helps quantify whether the benefits justify the cost for your specific situation.
>
> **Finding 3 - Rolling is the Safe Fallback:**
> When Blue-Green isn't feasible—maybe you don't have spare capacity, or your infrastructure doesn't support it—Rolling is the reliable choice. It's not the fastest, but it guarantees availability is maintained throughout the process.
>
> Rolling's moderate performance (315s, mid-range exposure) makes it the "safe middle ground." It's what most organizations should default to when they can't do Blue-Green.
>
> **Finding 4 - Constraint-Aware Planning Works:**
> Here's a validation of our approach: all six strategies that succeeded (everything except Big Bang) achieved **zero service-level downtime**. The total_downtime_seconds_overall metric—which measures time when fewer than min_up instances were healthy—was zero across the board.
>
> This means our planning algorithms correctly calculate max_down per service and never violate constraints. The simulation validates that the plans are sound before you execute them in production.
>
> **Finding 5 - Quantitative Metrics Enable Objective Comparison:**
> Perhaps the most important finding is methodological: by defining clear metrics—exposure window, unavailability, rollbacks, mixed version time—we transform a subjective debate ("which strategy is better?") into an objective analysis.
>
> Different organizations have different priorities. If security exposure is your top concern, minimize the exposure metric. If you're optimizing for operational simplicity, minimize rollbacks. If user experience is paramount, minimize unavailability. The framework gives you the data to make these trade-offs explicitly rather than implicitly.

---

## Slide 10: Conclusions & Future Work

### Conclusions

- Naive strategies don't work for critical systems
- Blue-Green optimal when capacity is available
- Framework provides **quantitative decision support**

### Future Directions

| Direction | Description |
|-----------|-------------|
| 🧬 Auto-optimization | Genetic algorithms for optimal plans |
| 🔄 Dynamic scenarios | Handle changes during execution |
| 💰 Cost modeling | Include capacity costs in trade-offs |
| 🏭 Real validation | Test on production infrastructure |
| 🖥️ GUI | Real-time visualization interface |

### Thank You!

**Questions?**

### 📝 Speaker Notes (Slide 10)

> Let me wrap up with our conclusions and discuss where this research could go next.
>
> **Main Conclusions:**
>
> First, we've demonstrated empirically that naive approaches fail. "Patch everything now" sounds fast, but it's not viable for any system that needs to stay running. This validates the need for sophisticated, constraint-aware planning.
>
> Second, when you can afford it, Blue-Green is the optimal strategy. It achieves the best results across all metrics. If you're designing new infrastructure, build in the capacity for Blue-Green deployments—your future self will thank you during patching windows.
>
> Third, and perhaps most importantly, this framework enables **quantitative decision support**. Instead of debating strategies based on intuition or past experience, operators can now simulate their specific infrastructure, see the numbers, and make informed decisions. This is the real contribution: turning a qualitative problem into a quantitative one.
>
> **Future Directions:**
>
> We see five promising areas for extending this work:
>
> 1. **Automatic Optimization:** Currently, we compare predefined strategies. Future work could use optimization techniques—genetic algorithms, simulated annealing—to automatically generate optimal plans for a given infrastructure. Instead of "which of these 7 strategies is best?", the system would synthesize a custom strategy.
>
> 2. **Dynamic Scenarios:** Our current model assumes the infrastructure is static during patching. In reality, nodes might fail independently, new urgent patches might arrive mid-execution, or traffic patterns might change. Extending the simulator to handle dynamic events would increase realism.
>
> 3. **Cost Modeling:** Blue-Green requires extra capacity, but how much does that cost? Future versions could incorporate financial models—cloud instance pricing, energy costs, opportunity costs—to provide complete trade-off analysis including economic factors.
>
> 4. **Real-World Validation:** We've validated the framework through simulation, but the ultimate test is production deployment. Partnering with organizations to test PatchPlanner on real infrastructure would validate our models and identify gaps.
>
> 5. **Graphical Interface:** Currently, PatchPlanner is command-line driven. A web-based GUI that lets operators visualize their infrastructure graph, watch simulations play out in real-time, and interactively explore different strategies would make the tool more accessible.
>
> **Closing:**
>
> PatchPlanner demonstrates that the security-availability trade-off, while real, is not insurmountable. With the right tools and data, we can find strategies that protect systems from vulnerabilities without sacrificing the availability that makes them valuable in the first place.
>
> Thank you for your attention. I'm happy to take questions about the methodology, the implementation, or the results.

---

## Backup Slide: Visual Comparison

### Completion Time (Scenario 1)

```
BlueGreen  ████████ 120s
Rolling    ███████████████████████████ 315s  
Canary     █████████████████████████████████ 375s
Batch      █████████████████████████████████████████████████████████ 630s
DepGreedy  ████████████████████████████████████████████████████████████████████████████████████████ 960s
Hybrid     █████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████ 1350s
```

### Exposure Window (Scenario 1)

```
BlueGreen  ██████████ 47,160
Rolling    ██████████████████████████ 90,150
Canary     ██████████████████████████████ 106,920
Batch      █████████████████████████████████████████████████████ 162,255
DepGreedy  ██████████████████████████████████████████████████████████████████████████████████████████ 202,440
Hybrid     ████████████████████████████████████████████████████████████████████████████████████████████████████████████████ 247,455
```

### 📝 Speaker Notes (Backup Slide)

> This backup slide provides visual comparisons in case you want to emphasize the magnitude of differences between strategies.
>
> **Completion Time Chart:**
> Notice how Blue-Green (120s) is dramatically faster than everything else. The bar is less than half the length of Rolling (315s). And look at Hybrid—at 1,350 seconds, it's over 11 times longer than Blue-Green!
>
> This visualization makes it viscerally clear: if speed matters, Blue-Green is in a different league. The question becomes whether you can afford the extra capacity it requires.
>
> **Exposure Window Chart:**
> The pattern is similar for security exposure. Blue-Green's exposure (47,160) is about half of Rolling's (90,150). But notice something interesting: the exposure for slower strategies (Hybrid at 247,455) is actually worse than faster strategies.
>
> This might seem counterintuitive—shouldn't a more careful strategy have better security? But remember: exposure is cumulative over time. Even though Hybrid is more careful at each step, it takes so much longer that nodes remain unpatched for extended periods, accumulating exposure.
>
> This insight is important: **being overly cautious can actually harm security** because it extends the vulnerability window. There's a "Goldilocks zone" where you're careful enough to maintain availability but fast enough to minimize exposure. Blue-Green hits this zone perfectly; Hybrid overshoots on caution.
>
> Use this slide if the audience needs to understand the relative magnitudes, or if someone questions whether the differences are meaningful. The visual makes it undeniable.

