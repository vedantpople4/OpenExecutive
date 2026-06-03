# Case Studies

This document contains real-world business decisions and outcomes from TechNova's first 18 months of operation.

---

## Case Study 1: GPU Acquisition Decision (Q3 2023)

### Decision Point
Should TechNova purchase 5,000 H100 GPUs outright or lease them on AWS?

### Background
- Cash position: $38M post-Series B
- Annual growth target: 300% (need 40,000 GPU hours/month)
- AWS lease cost: $2.00/GPU-hour (on-demand), $1.50 (12-month commitment)
- Direct H100 cost: $12,000/unit (lead time: 4-6 weeks)

### Options Evaluated

**Option A: Buy 5,000 H100s outright**
- Capital expenditure: $60M
- Requires: Data center build-out, power/cooling (~$5M additional)
- Ownership: Full control, can resell if demand drops

**Option B: AWS lease with commitment**
- Monthly spend: $40M (40,000 hours × $2.00)
- Commitment: 12-month minimum
- Flexibility: Can scale up/down with demand

**Option C: Hybrid approach**
- Buy 2,000 H100s: $24M capital
- Lease 30,000 GPU-hours on AWS for peak demand
- Maintain 50% buffer capacity

### Board Decision
**Chose Option C (Hybrid)**
- Rationale: Balance capital efficiency with demand certainty
- 2,000 H100s acquired in Q4 2023
- AWS lease for 30,000 GPU-hours/month

### Outcome (6 months post-decision)

| Metric | Target | Actual | Variance |
|--------|--------|--------|----------|
| GPU capacity utilization | 70% | 65% | -5% |
| Monthly spend | $25M | $28M | +12% |
| Customer growth | 200 customers | 140 customers | -30% |
| Revenue | $8M ARR | $5.5M ARR | -31% |

### Lessons Learned

**What went well:**
- Capital efficiency: Only committed $24M upfront vs. $60M
- Flexibility maintained ability to scale

**What went wrong:**
- Growth projections were 30% too optimistic
- AWS lease costs exceeded budget due to on-demand usage
- Data center readiness delayed by 3 weeks

**Key insight:** Growth-dependent capacity planning creates dangerous overcommitment risk. Future decisions should use conservative (50%) growth assumptions.

---

## Case Study 2: Kubernetes Platform Decision (Q1 2024)

### Decision Point
Should we build a Kubernetes-native platform or integrate with existing cloud offerings (AWS EKS, GKE)?

### Background
- Customer requests for native K8s increased to 60% of enterprise inquiries
- Build estimate: 18 months, 15 engineers, $12M cost
- Integration estimate: 4 months, 5 engineers, $3M cost

### Options Evaluated

**Option A: Build native K8s platform**
- Timeline: 18 months to MVP
- Cost: $12M total
- Control: Full feature ownership

**Option B: Build K8s integrations**
- Timeline: 4 months
- Cost: $3M
- Dependency: AWS EKS, GKE reliability

**Option C: No K8s support (status quo)**
- Risk: Lose K8s-focused customers
- Revenue impact: Estimated $2M ARR at risk

### Board Decision
**Chose Option B (Integrations)**
- Rationale: Speed to market, lower risk, leverage existing infrastructure
- Plan: Re-evaluate native platform after 12 months

### Outcome (3 months post-decision)

| Metric | Target | Actual | Variance |
|--------|--------|--------|----------|
| Time to market | 4 months | 4 months | 0% |
| Cost | $3M | $2.8M | -7% |
| Customer adoption | 40% | 75% | +87% |
| New K8s customers | 10 | 8 | -20% |

### Lessons Learned

**What went well:**
- Fast delivery, under budget
- 75% of existing customers adopted within 3 months
- No technical debt from rushed feature

**What went wrong:**
- AWS EKS outages affected customer trust
- Lost 3 customers who wanted on-prem K8s
- Feature requests from K8s users blocked by AWS roadmap

**Key insight:** Third-party dependencies create hidden costs in reliability and feature velocity. For mission-critical enterprise features, consider native implementation.

---

## Case Study 3: Enterprise Sales Hire Decision (Q2 2023)

### Decision Point
Should TechNova hire 3 senior enterprise account executives at $250K total comp each, or continue with founding team sales?

### Background
- Sales cycle length: 6 months average
- Average deal size: $400K ARR
- Current sales capacity: 15 deals in pipeline (founding team managing)
- Conversion rate: 35% (above industry 25% benchmark)

### Options Evaluated

**Option A: Hire 3 AEs**
- Annual cost: $750K (salary + commissions)
- Expected capacity: 12 deals/hander
- Ramp time: 3 months

**Option B: Hire 1 AE + 1 SDR**
- Annual cost: $350K
- Expected capacity: 6 deals/hander
- SDR handles prospecting, AE handles closing

**Option C: No hires**
- Risk: Burnout, missed deadlines, deals slipping

### Board Decision
**Chose Option A (3 AEs)**
- Rationale: Pipeline growth requires capacity, not just prospecting
- Founders will transition to strategic accounts

### Outcome (6 months post-hire)

| Metric | Target | Actual | Variance |
|--------|--------|--------|----------|
| Revenue | $6M ARR | $8M ARR | +33% |
| Deals closed | 12 | 15 | +25% |
| Sales cycle | 6 months | 5 months | -17% |
| AE retention | 100% | 67% | -33% |

### Lessons Learned

**What went well:**
- Revenue exceeded targets by 33%
- Sales cycle shortened (learning curve)
- Founders freed up for product strategy

**What went wrong:**
- 1 AE left after 4 months (joined competitor)
- Customer satisfaction scores dipped 5 points
- Product/engineering capacity stretched (support requests)

**Key insight:** Enterprise sales hiring requires careful cultural fit assessment, not just revenue track record. Also need to align sales targets with engineering capacity.

---

## Case Study 4: Security Certification Decision (Q4 2023)

### Decision Point
Should TechNova pursue FedRAMP authorization ($2M, 18 months) or wait for customer demand?

### Background
- Healthcare vertical: $3M ARR, 25% YoY growth
- Federal contracts: 0 (blocked by FedRAMP requirement)
- Healthcare customers requesting FedRAMP: 2

### Options Evaluated

**Option A: Pursue FedRAMP**
- Cost: $2M (consultants + internal effort)
- Timeline: 18 months
- Market access: $50B federal market

**Option B: Delay, wait for demand**
- Risk: Lose 2 potential customers ($1M ARR at risk)
- Cost: $0
- Flexibility: Can reassess when 5+ requests

**Option C: SOC2 Type II first**
- Cost: $200K
- Timeline: 6 months
- Market access: General enterprise, not federal

### Board Decision
**Chose Option A (FedRAMP)**
- Rationale: Healthcare growth indicates federal pathway is viable
- First-mover advantage in regulated AI infrastructure

### Outcome (12 months post-decision)

| Metric | Target | Actual | Variance |
|--------|--------|--------|----------|
| FedRAMP certification | 18 months | 24 months | +33% |
| Cost | $2M | $2.5M | +25% |
| Federal deals won | 0 | 1 | -50% (1 expected) |
| Healthcare growth | 25% | 35% | +10% |

### Lessons Learned

**What went well:**
- Healthcare growth exceeded expectations (35%)
- SOC2 Type II achieved (interim milestone)
- Federal deal won (first of 3 expected)

**What went wrong:**
- Timeline slip by 6 months
- Budget overrun by $500K
- Federal procurement process slower than anticipated

**Key insight:** Government procurement cycles are longer than anticipated. Certifications help, but relationship building and proof points matter more initially. Consider parallel paths: pursue certification while building federal relationships.

---

## Summary Insights

### Common Decision Patterns

1. **Growth assumptions matter:** Conservative assumptions prevent overcommitment
2. **Build vs. buy tradeoffs:** Speed often wins, but consider hidden dependency costs
3. **Hiring quality > speed:** Bad hires cost more than delayed hires
4. **Certification ROI:** Hard to predict, but early investment compounds

### Decision Framework Recommendations

For future board decisions:
- Always run scenarios with 50% conservative vs. optimistic assumptions
- Document decision rationale for post-mortem learning
- Set clear review points (3-month check-ins for major decisions)
- Track "decision cost of delay" vs. "decision risk of wrong choice"
