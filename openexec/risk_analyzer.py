#!/usr/bin/env python3
"""Risk quantification and analysis for OpenExec."""

import re
from typing import Dict, Any, List

# Agents tag their own risks per output schema, e.g. "Probability: High" or
# "[probability: Med]". An explicit tag beats keyword guessing.
_PROB_TAG_RE = re.compile(r"probability:?\s*\(?\s*(high|med(?:ium)?|low)", re.IGNORECASE)
_TAG_PROBABILITIES = {"high": 0.8, "med": 0.5, "medium": 0.5, "low": 0.2}


class RiskQuantifier:
    """Quantifies risks with probability and impact scoring."""

    def __init__(self):
        self.risk_patterns = {
            'burn': {'probability': 0.7, 'impact': 8},
            'runway': {'probability': 0.6, 'impact': 9},
            'bankrupt': {'probability': 0.4, 'impact': 10},
            'obsolescence': {'probability': 0.5, 'impact': 6},
            'debt': {'probability': 0.6, 'impact': 7},
            'market': {'probability': 0.5, 'impact': 7},
            'competitive': {'probability': 0.4, 'impact': 6},
            'regulatory': {'probability': 0.3, 'impact': 8},
        }

    def quantify_risk(self, risk_text: str) -> Dict[str, Any]:
        """Quantify a single risk based on text analysis."""
        risk_lower = risk_text.lower()

        # Default values
        probability = 0.5
        impact = 5
        mitigation_cost = "Medium"

        # Check for patterns
        for pattern, scores in self.risk_patterns.items():
            if pattern in risk_lower:
                probability = scores['probability']
                impact = scores['impact']
                break

        # An explicit probability tag from the agent overrides the keyword guess
        tag_match = _PROB_TAG_RE.search(risk_text)
        if tag_match:
            probability = _TAG_PROBABILITIES[tag_match.group(1).lower()]

        # Adjust based on agent (CEO/CFO risks are typically higher impact)
        if '[CEO]' in risk_text or '[CFO]' in risk_text:
            impact = min(10, impact + 1)

        # Calculate risk score
        risk_score = probability * impact

        return {
            'text': risk_text,
            'probability': probability,
            'impact': impact,
            'risk_score': risk_score,
            'mitigation_cost': mitigation_cost,
            'priority': self._get_priority(risk_score)
        }

    def _get_priority(self, risk_score: float) -> str:
        """Get priority based on risk score."""
        if risk_score >= 7:
            return "HIGH"
        elif risk_score >= 4:
            return "MEDIUM"
        else:
            return "LOW"

    def _impact_band(self, impact: int) -> str:
        """Map impact score to band label."""
        if impact >= 9:
            return "Critical"
        elif impact >= 7:
            return "High"
        elif impact >= 4:
            return "Med"
        return "Low"

    def _prob_band(self, probability: float) -> str:
        """Map probability to band label."""
        if probability >= 0.7:
            return "High"
        elif probability >= 0.4:
            return "Med"
        return "Low"

    def generate_risk_matrix(self, risks: List[str]) -> str:
        """Generate dynamic ASCII risk matrix with plotted risks."""
        quantified = [self.quantify_risk(risk) for risk in risks]

        # Build a 3x4 grid: prob levels (High, Med, Low) x impact levels (Critical, High, Med, Low)
        # Rows: probability (top to bottom: High, Med, Low)
        # Cols: impact (left to right: Low, Med, High, Critical)
        prob_levels = ["High", "Med", "Low"]
        impact_levels = ["Low", "Med", "High", "Critical"]

        # Collect markers per cell
        cell_markers: Dict[str, Dict[str, List[str]]] = {p: {i: [] for i in impact_levels} for p in prob_levels}
        for risk in quantified:
            p_band = self._prob_band(risk['probability'])
            i_band = self._impact_band(risk['impact'])
            # Priority letter for marker
            letter = risk['priority'][0]  # H, M, L
            cell_markers[p_band][i_band].append(letter)

        # Build grid rows
        lines = []
        lines.append("Risk Matrix:")
        lines.append("            IMPACT ->")
        lines.append("            Low   Med   High  Critical")

        for prob in prob_levels:
            if prob == "High":
                row_label = "PROBABIL  High"
            elif prob == "Med":
                row_label = "ITY    ↑  Med"
            else:
                row_label = "         Low"

            cells = []
            for impact in impact_levels:
                markers = cell_markers[prob][impact]
                if markers:
                    # Unique markers, sorted
                    unique_markers = sorted(set(markers))
                    cell_text = "[" + "".join(unique_markers) + "]"
                else:
                    cell_text = " .   "
                cells.append(cell_text)
            lines.append(f"{row_label}  {cells[0]}  {cells[1]}  {cells[2]}  {cells[3]}")

        lines.append("")
        lines.append("Legend: [H]=High priority, [M]=Medium priority, [L]=Low priority")
        lines.append("")

        # Add detailed breakdown
        lines.append("## Quantified Risks")
        lines.append("")
        for risk in sorted(quantified, key=lambda x: x['risk_score'], reverse=True)[:10]:
            lines.append(f"- {risk['priority']} | P:{risk['probability']:.0%} | I:{risk['impact']}/10 | Score:{risk['risk_score']:.1f}")
            lines.append(f"  {risk['text'][:80]}...")
            lines.append("")

        return '\n'.join(lines)


def quantify_risks(results: Dict[str, Any]) -> Dict[str, Any]:
    """Add risk quantification to results."""
    quantifier = RiskQuantifier()

    all_risks = results.get('overall_risk_assessment', [])
    quantified_risks = [quantifier.quantify_risk(risk) for risk in all_risks]

    # Sort by risk score
    quantified_risks.sort(key=lambda x: x['risk_score'], reverse=True)

    results['quantified_risks'] = quantified_risks
    results['risk_matrix'] = quantifier.generate_risk_matrix(all_risks)

    return results
