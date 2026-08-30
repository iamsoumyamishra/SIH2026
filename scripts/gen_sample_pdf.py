from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

path = "sample_documents/inspection_report.pdf"
doc = SimpleDocTemplate(path, pagesize=A4)
styles = getSampleStyleSheet()
story = []
story.append(Paragraph("Inspection Report - Machine ID: MC-1042", styles["Title"]))
story.append(Spacer(1, 12))
story.append(Paragraph("Inspection Date: 2026-08-20   Inspector: J. Alvarez", styles["Normal"]))
story.append(Spacer(1, 12))
story.append(Paragraph("Findings Summary", styles["Heading2"]))
data = [
    ["Checklist Item", "Status", "Remark"],
    ["Bearing vibration level", "FAIL", "Vibration exceeds threshold (7.2 mm/s vs 4.5 limit)"],
    ["Oil level check", "PASS", "Within specified range"],
    ["Coupling alignment", "FAIL", "Misalignment detected, offset 0.9 mm"],
    ["Coolant temperature", "PASS", "Within tolerance"],
    ["Belt tension", "FAIL", "Tension below minimum, needs retightening"],
]
t = Table(data)
t.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ]
    )
)
story.append(t)
story.append(Spacer(1, 12))
story.append(Paragraph("Recommended action: Perform corrective maintenance and re-inspect.", styles["Normal"]))
doc.build(story)
print("wrote", path)
