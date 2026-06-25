import json
import os

knowledge_path = 'knowledge/diseases.json'

with open(knowledge_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

treatments = {
    "Common Cold": ["Over-the-counter decongestants (e.g., pseudoephedrine)", "Antihistamines for runny nose", "NSAIDs or acetaminophen for fever and pain", "Cough suppressants (dextromethorphan)"],
    "Flu": ["Antiviral drugs (e.g., Oseltamivir/Tamiflu) if diagnosed early", "NSAIDs (Ibuprofen) or Acetaminophen for fever/aches", "IV fluids in severe cases"],
    "Pneumonia": ["Antibiotics (e.g., Azithromycin, Amoxicillin) for bacterial pneumonia", "Antivirals for viral pneumonia", "Corticosteroids for severe inflammation", "Oxygen therapy in severe cases"],
    "Diabetes": ["Insulin therapy (Type 1 or advanced Type 2)", "Metformin (first-line for Type 2)", "Sulfonylureas or SGLT2 inhibitors", "Regular blood glucose monitoring"],
    "Hypertension": ["ACE inhibitors (e.g., Lisinopril)", "Angiotensin II receptor blockers (ARBs)", "Diuretics (e.g., Hydrochlorothiazide)", "Calcium channel blockers", "Beta blockers"],
    "Migraine": ["Triptans (e.g., Sumatriptan) for acute attacks", "NSAIDs or specialized pain relievers", "Preventive medications (beta blockers, antidepressants, or anti-seizure drugs)", "CGRP antagonists"],
    "Dengue": ["Intravenous (IV) fluid and electrolyte replacement", "Acetaminophen for fever management", "Blood pressure monitoring", "Blood transfusion in severe hemorrhagic cases"],
    "Malaria": ["Artemisinin-based combination therapies (ACTs)", "Chloroquine phosphate", "Mefloquine or Quinine sulfate depending on resistance"],
    "Typhoid": ["Antibiotics (e.g., Ciprofloxacin, Azithromycin, or Ceftriaxone)", "Intravenous fluids for severe dehydration", "Surgery in case of intestinal perforation"],
    "Tuberculosis": ["Long-term antibiotic regimen (e.g., Isoniazid, Rifampin, Ethambutol, Pyrazinamide) for 6-9 months", "Directly observed therapy (DOT)"],
    "Asthma": ["Inhaled corticosteroids (e.g., Fluticasone)", "Short-acting beta agonists (e.g., Albuterol) for rescue", "Long-acting beta agonists (LABAs)", "Leukotriene modifiers"],
    "Bronchitis": ["Bronchodilators (inhalers) to open airways", "Cough suppressants", "Antibiotics (only if a bacterial infection is identified)", "Corticosteroids to reduce inflammation"],
    "Gastroenteritis": ["Oral Rehydration Salts (ORS)", "Anti-emetics (e.g., Ondansetron) for nausea", "Anti-diarrheal medication (e.g., Loperamide) in specific cases", "IV fluids for severe dehydration"],
    "Urinary Tract Infection": ["Antibiotics (e.g., Nitrofurantoin, Trimethoprim-sulfamethoxazole, or Fosfomycin)", "Phenazopyridine for urinary pain relief"],
    "Anemia": ["Iron supplements (ferrous sulfate)", "Vitamin B12 injections", "Folic acid supplements", "Erythropoiesis-stimulating agents (ESAs) in severe chronic cases"],
    "Arthritis": ["NSAIDs (e.g., Ibuprofen, Naproxen, Celecoxib)", "Corticosteroids (injections or oral)", "Disease-modifying antirheumatic drugs (DMARDs) like Methotrexate for RA", "Biologic response modifiers"],
    "Chicken Pox": ["Antiviral medications (e.g., Acyclovir) for high-risk patients", "Calamine lotion and colloidal oatmeal baths", "Antihistamines for severe itching", "Acetaminophen for fever (Avoid Aspirin)"],
    "Jaundice": ["Treatment targets the underlying cause (e.g., antiviral meds for Hepatitis)", "Phototherapy (primarily for newborns)", "Surgical removal of gallstones if they are the cause", "Liver transplant in cases of severe liver failure"],
    "Hepatitis": ["Antiviral medications (e.g., Entecavir, Tenofovir for Hep B; Sofosbuvir for Hep C)", "Interferon injections", "Supportive care and monitoring", "Liver transplantation for end-stage liver disease"],
    "Allergic Rhinitis": ["Intranasal corticosteroids (e.g., Fluticasone spray)", "Oral antihistamines (e.g., Cetirizine, Loratadine)", "Decongestants", "Allergen immunotherapy (allergy shots)"],
    "Sinusitis": ["Nasal corticosteroids", "Saline nasal irrigation", "Antibiotics (e.g., Amoxicillin) if bacterial infection is suspected", "Decongestants (short-term use)"],
    "Vertigo": ["Vestibular rehabilitation therapy (VRT)", "Epley maneuver (for BPPV)", "Meclizine or Prochlorperazine for nausea/dizziness", "Diuretics (for Meniere's disease)"],
    "Acne": ["Topical retinoids (e.g., Tretinoin, Adapalene)", "Benzoyl peroxide", "Topical or oral antibiotics (e.g., Doxycycline)", "Isotretinoin for severe cystic acne", "Oral contraceptives (for hormonal acne)"],
    "Eczema": ["Topical corticosteroids (various strengths)", "Calcineurin inhibitors (e.g., Tacrolimus)", "Injectable biologics (e.g., Dupilumab) for severe cases", "Phototherapy"],
    "Psoriasis": ["Topical corticosteroids", "Vitamin D analogues (e.g., Calcipotriene)", "Systemic medications (Methotrexate, Cyclosporine)", "Biologic therapies (e.g., Adalimumab, Secukinumab)", "Phototherapy"],
}

generic_treatment = [
    "Consult a healthcare professional for a personalized treatment plan.",
    "Prescription medications may be required based on the severity and underlying cause.",
    "Do not self-medicate with antibiotics or prescription drugs without medical supervision."
]

for disease in data:
    if disease in treatments:
        data[disease]["clinical_treatments"] = treatments[disease]
    else:
        # Generate a generic one
        data[disease]["clinical_treatments"] = generic_treatment

with open(knowledge_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("Updated diseases.json successfully.")
