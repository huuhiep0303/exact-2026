"""
Topic hints for Magnetism & Electromagnetic Induction — prefix DDT.

Covers all 130 DDT questions:
  - Solenoid magnetic field (B = μ₀nI)
  - Inductance (L = μ₀N²A/l)
  - Magnetic flux (Φ = BAcosθ)
  - Faraday's law / induced EMF
  - Energy in inductor (W = ½LI²)
  - Lorentz force / force on current-carrying wire
  - Qualitative questions (proportionality, description, changes)
"""
import re
from typing import List


def _detect_qualitative(question: str) -> List[str]:
    """Detect qualitative questions that need text answers, not numbers."""
    hints = []
    q = question.lower()

    qual_patterns = [
        (r"proportional to", "proportionality"),
        (r"tỷ lệ thuận", "proportionality"),
        (r"how does.+change", "change description"),
        (r"thay đổi.+thế nào", "change description"),
        (r"what happens", "description"),
        (r"what are the characteristics", "description"),
        (r"đặc điểm", "description"),
        (r"what is the direction", "direction"),
        (r"hướng", "direction"),
        (r"increases or decreases", "change description"),
        (r"tăng hay giảm", "change description"),
        (r"doubled|tripled|halved", "change description"),
        (r"gấp đôi|gấp ba|giảm một nửa", "change description"),
    ]

    for pattern, ptype in qual_patterns:
        if re.search(pattern, q):
            if ptype == "proportionality":
                hints.append(
                    "QUALITATIVE ANSWER: The question asks what a quantity is "
                    "proportional to. Answer with a descriptive string, e.g. "
                    "'Number of turns density and current intensity'. "
                    "Set unit = '-'."
                )
            elif ptype == "change description":
                hints.append(
                    "QUALITATIVE ANSWER: The question asks how a quantity "
                    "changes. Answer with a description, e.g. 'Doubled', "
                    "'Halved', 'Does not change'. Set unit = '-'."
                )
            elif ptype == "description":
                hints.append(
                    "QUALITATIVE ANSWER: The question asks for a description "
                    "or characteristic. Answer with a descriptive text. "
                    "Do NOT invent numbers. Set unit = '-'."
                )
            elif ptype == "direction":
                hints.append(
                    "QUALITATIVE ANSWER: The question asks for direction. "
                    "Use the right-hand rule. Answer with text description."
                )
            break  # only emit one qualitative hint

    return hints


def _detect_solenoid(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["solenoid", "ống dây", "cuộn dây"]):
        hints.append(
            "Solenoid field: B = μ₀ · n · I, where n = N/l (turns per metre). "
            "μ₀ = 4π × 10⁻⁷ H/m. "
            "Convert l from cm to m, and use N (total turns)."
        )
        hints.append(
            "Solenoid inductance: L = μ₀ · N² · A / l. "
            "Convert area from cm² to m²."
        )
    return hints


def _detect_flux(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["flux", "từ thông", "phi", "Φ"]):
        hints.append(
            "Magnetic flux: Φ = B · A · cos(θ), where θ is the angle "
            "between B and the normal to the surface. "
            "If B is perpendicular to the surface, θ = 0 → Φ = B·A."
        )
    return hints


def _detect_induced_emf(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["emf", "induced", "suất điện động",
                               "cảm ứng", "faraday"]):
        hints.append(
            "Induced EMF: |e| = |ΔΦ/Δt| = N · |ΔΦ/Δt| for N-turn coil. "
            "Or |e| = L · |ΔI/Δt| for self-induction."
        )
    return hints


def _detect_energy(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["energy", "năng lượng"]) and \
       any(kw in q for kw in ["inductor", "cuộn cảm", "magnetic", "từ"]):
        hints.append(
            "Energy stored in inductor: W = ½ · L · I². "
            "Magnetic energy density: w = B² / (2μ₀)."
        )
    return hints


def _detect_force(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["lorentz", "moving charge", "điện tích chuyển"]):
        hints.append("Lorentz force: F = q · v · B · sin(α).")
    if any(kw in q for kw in ["current-carrying", "dây dẫn mang dòng",
                               "wire in magnetic"]):
        hints.append("Force on wire: F = B · I · l · sin(α).")
    return hints


def analyze(question: str) -> List[str]:
    """Return all applicable magnetism/induction hints."""
    hints: List[str] = []
    hints.extend(_detect_qualitative(question))
    hints.extend(_detect_solenoid(question))
    hints.extend(_detect_flux(question))
    hints.extend(_detect_induced_emf(question))
    hints.extend(_detect_energy(question))
    hints.extend(_detect_force(question))
    return list(dict.fromkeys(hints))
