{
    "title": "Toward predicting vitamin D levels without a blood test.",
    "slug": "toward-predicting-vitamin-d-levels-without-a-blood-test",
    "aliases": [
        "/Toward+predicting+vitamin+D+levels+without+a+blood+test",
        "/4847"
    ],
    "tiki_page_id": 4847,
    "date": "2013-12-03",
    "categories": [
        "Top news",
        "Predict"
    ],
    "tags": [
        "NAFLD",
        "Predict",
        "Top news",
        "antibiotics",
        "cardiovascular",
        "child",
        "cholesterol",
        "depression",
        "depression and pregnancy",
        "dosage",
        "health risk",
        "liver",
        "magnesium",
        "magnesium and pregnancy",
        "mood disorders",
        "omega 3",
        "omega 3 and pregnancy",
        "pollution",
        "pregnancy",
        "probiotics",
        "smoking",
        "statins",
        "vitamin d"
    ],
    "associated_tags": [
        "CYPA",
        "CYPB",
        "CYPR",
        "EBV",
        "HRV",
        "PCOS",
        "RSV",
        "SAD",
        "ankle fractures",
        "anxiety",
        "asthma",
        "atherosclerosis",
        "atrial fibrillation",
        "autoimmune",
        "bacteria",
        "bird flu",
        "bladder cancer",
        "blood clotting",
        "bone",
        "bone health",
        "bone loss",
        "bone mineral density",
        "bone stress fractures",
        "breast cancer",
        "breastfed",
        "breathing",
        "caesarean",
        "calcium",
        "cancer",
        "cancers after vaccination",
        "childhood vaccination effects",
        "children fractures",
        "colon cancer",
        "cystic fibrosis",
        "dark skin and pregnancy",
        "dengue",
        "diabetes",
        "endometrial cancer",
        "endometriosis",
        "epigenetics",
        "excess deaths",
        "falls fractures",
        "fertility sperm",
        "gastric cancer",
        "genetics",
        "gestational diabetes",
        "gut microbiome",
        "hay fever",
        "head and neck cancer",
        "heart failure",
        "helicobacter pylori",
        "hemodialysis",
        "herpes shingles",
        "high dose",
        "hip fractures",
        "immune dysfunction",
        "immune response",
        "immune system",
        "in vitro fertilization",
        "infection",
        "inflammation",
        "influenza",
        "iodine",
        "ivermectin",
        "leukemia",
        "liver cancer",
        "long covid",
        "low birth weight",
        "lung cancer",
        "lupus",
        "lymphoma",
        "magnesium and viruses",
        "masks",
        "melanoma",
        "metabolic",
        "metabolic syndrome",
        "miscarriage",
        "mononucleosis",
        "multiple myeloma",
        "multiple sclerosis",
        "multiple sclerosis and pregnancy",
        "muscle function",
        "neuropathy",
        "obesity",
        "omega 3 and viruses",
        "osteoporosis",
        "ovarian cancer",
        "pancreatic cancer",
        "pfizer",
        "phosphorus",
        "placenta",
        "pneumonia",
        "prediabetes",
        "preeclampsia",
        "preterm",
        "preterm and omega 3",
        "prostate cancer",
        "red meat",
        "respiratory",
        "retinopathy",
        "rheumatoid arthritis",
        "rickets",
        "skin cancer",
        "stillbirth",
        "stroke",
        "systemic sclerosis",
        "telomere",
        "therapeutic intervention",
        "thyroid cancer",
        "tuberculosis",
        "type 1 diabetes",
        "ultraviolet light",
        "urinary tract infection",
        "vaccination",
        "vaccination and pregnancy",
        "viral hepatitis",
        "virus",
        "virus and air pollution",
        "virus and cardiovascular",
        "virus and cognitive",
        "virus and dark skin",
        "virus meta analyses",
        "virus studies",
        "viruses and pregnancy",
        "viruses and vitamin d receptor",
        "vitamin d and viruses",
        "vitamin d binding",
        "vitamin d deficiency",
        "vitamin d receptor",
        "vitamin k",
        "vitamin k and viruses",
        "wound healing",
        "zinc",
        "zinc and viruses"
    ]
}


{{< toc >}} 

---

#### Many models have failed to predict vitamin D levels based on about 10 variables.

 **The problems appear to be due to:** 

1. Not enough variables in the model

1. Not enough subjects

1. Not powerful enough software/model

1. Large variance between vitamin D testers ( 5% to 10%)

1. Not record other health influences - emotional stress as a child, antibiotics as a child

#### VitaminDWiki is considering solving all of the above problems

* Might be able to predect vitamin D test results to be in one of the following ranges

> 0-20 15-25 20-30 25-35 30-50  40-60  50-70 60-80 70-100 80–100+

> Goal of model: less than 5% chance of being in an adjacent category

> Goal of model: 10X less chance (0.5%) of being off by 2 categories

> &nbsp; &nbsp; &nbsp;   Example: predicted 20-30 ng but was actually 30-50 ng

* Vast majortiy of the data samples will be in the range of 10-30 ng

* Age range: 18 ==> 100 – majority in the range of 30-80

* Data for training and testing the model might be crowd-sourced via the web

> People could fill in both the variables AND their vitamin D test results

> Rarely can we expect that all of the variables will be filled in

> Especially expect to lack the model of the tester

#### Variables/questions

Will need to quantize the details to train a model with the data

Might want to provide the user an indication of the importance of each question.

##### Age

##### Body

Weight, BMI, Muscular (compensates for BMI in-accuracy)

[Skin color](/tags/skin-color.html)

[Red hair](/tags/red-hair.html) (less likely to be out in the sun)

##### Have a disease/health problem which is strongly associated with low vitamin D

[Trauma, Surgery](https://www.VitaminDWiki.com/Trauma+and+surgery)

plasma exchange – reduces vitami D level by 50% in a single day

Inflammation – including depression -which consumes vitamin D

Have infection

[Gut](/tags/gut.html), Kidney, liver poor

Low stomach acid ==> less Magnesium

Fatty liver disease

Sore bones

No gall bladder

Poor sleep

##### Female

On the pill

Currently pregnant or lactating

Pregnancy during past 12 months

Twins during past 12 months

Excessive clothing for reliigious reasons

##### What is consumed

Vitamin D supplements : e.g. 400 IU, 4,000 IU (more than 3 months)  D2 vs D3

Take Vitamin D3 supplements with evening meal or monsaturated fats

Magnesium supplements  > 300 mg of Mg increases vitamin D levels about 30%, Mag in hard water

Probiotics

Low cholesterol diet

HFCS, pop

Omega-3

Vitamin A

Low cholesterol diet

Does not drink fortified milk

Smoking

##### Drugs increase/decrease response

statins

##### Environment/access to sun in the middle of the day

Urban/rural

Season

Latitude

Recent suncation

Outdoor worker

Work second shift

Work long hours

Altitude (30% more UV at the altitude of Colorado)

Shut-in

Air pollution – reduces UVB and likelihood that person will go outdoors

Use air conditioing  (home, work, car)

Tanning bed use

Getting sunshine thru window > 3 hours a day for – UVA decreases vitamin D levels

Note: Vitamin D is not a constant  Canadian vitamin D levels fell by 6% in 2 years (2009-2011)

 **<i class="fas fa-file-pdf" style="margin-right: 0.3em;"></i><a href="https://d378j1rmrlek7x.cloudfront.net/attachments/pdf/grassroots-questionnaire121012.pdf">Download a Grassroots Health 2013 questionaire </a>** 

 **<i class="fas fa-file-pdf" style="margin-right: 0.3em;"></i><a href="https://d378j1rmrlek7x.cloudfront.net/attachments/pdf/gfh-q-march-2019-40-pages-compressed.pdf">Download a Grassroots Health 2019 questionaire for Henry Lahore</a>** 

Want some visibility as to the confidence of each prediction.