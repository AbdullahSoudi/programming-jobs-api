"""
Configuration for Programming Jobs Mobile API.
Keywords, geo-filtering rules, categories, and settings.
"""

import os

# ─── App Categories (9 categories shown in the mobile app) ───
# Each category maps to routing keywords used to classify jobs.
# A single job can belong to multiple categories.

APP_CATEGORIES = {
    "android": {
        "name": "Android",
        "icon": "android",
        "keywords": [
            "android developer", "android engineer", "android",
            "kotlin developer", "kotlin", "jetpack compose",
            "mobile developer", "mobile engineer", "mobile application",
            "flutter developer", "flutter engineer", "flutter",
            "react native developer", "react native engineer", "react native",
            "dart developer", "mobile app developer", "app developer",
        ],
    },
    "ios": {
        "name": "iOS",
        "icon": "apple",
        "keywords": [
            "ios developer", "ios engineer", "ios",
            "swift developer", "swift", "swiftui",
            "mobile developer", "mobile engineer", "mobile application",
            "flutter developer", "flutter engineer", "flutter",
            "react native developer", "react native engineer", "react native",
            "dart developer", "mobile app developer", "app developer",
        ],
    },
    "backend": {
        "name": "Backend",
        "icon": "server",
        "keywords": [
            "backend", "back-end", "back end", "server-side", "server side",
            "api developer", "api engineer",
            "full-stack", "full stack", "fullstack",
            "python developer", "python engineer",
            "java developer", "java engineer",
            "golang", "go developer", "go engineer",
            "rust developer", "rust engineer",
            "ruby developer", "rails developer",
            "php developer", "php engineer",
            "node.js developer", "nodejs developer", "node developer",
            "django", "flask", "fastapi", "spring", "laravel", "express",
            ".net developer", "dotnet developer", "c# developer",
        ],
    },
    "frontend": {
        "name": "Frontend",
        "icon": "layout",
        "keywords": [
            "frontend", "front-end", "front end",
            "ui developer", "ui engineer",
            "full-stack", "full stack", "fullstack",
            "react developer", "react engineer", "next.js",
            "angular developer", "vue developer", "vue.js",
            "javascript developer", "js developer",
            "typescript developer", "ts developer",
            "css", "tailwind", "svelte",
            "web developer", "web engineer",
        ],
    },
    "devops": {
        "name": "DevOps & Cloud",
        "icon": "cloud",
        "keywords": [
            "devops", "dev ops", "dev-ops",
            "sre", "site reliability",
            "cloud engineer", "cloud developer", "cloud architect",
            "infrastructure engineer", "platform engineer",
            "kubernetes", "docker", "terraform", "ansible",
            "aws engineer", "azure engineer", "gcp engineer",
            "ci/cd", "jenkins", "github actions",
            "linux engineer", "systems engineer", "systems administrator",
            "network engineer", "network administrator",
        ],
    },
    "ai_ml": {
        "name": "AI/ML",
        "icon": "brain",
        "keywords": [
            "machine learning", "ml engineer", "ml developer",
            "ai engineer", "ai developer", "artificial intelligence",
            "deep learning", "nlp engineer", "computer vision",
            "data scientist", "data science",
            "data analyst", "data analytics",
            "data engineer", "etl developer", "data pipeline",
            "big data", "hadoop", "spark engineer",
            "llm", "generative ai", "prompt engineer",
            "tensorflow", "pytorch", "hugging face",
        ],
    },
    "cybersecurity": {
        "name": "Cybersecurity",
        "icon": "shield",
        "keywords": [
            "security engineer", "appsec", "application security",
            "cybersecurity", "cyber security", "infosec",
            "penetration tester", "pen tester", "security analyst",
            "soc analyst", "security architect",
            "vulnerability", "ethical hacker",
            "security operations", "threat",
        ],
    },
    "qa": {
        "name": "QA & Testing",
        "icon": "check-circle",
        "keywords": [
            "qa engineer", "qa developer", "quality assurance",
            "test engineer", "sdet", "software tester",
            "automation engineer", "test automation",
            "qa analyst", "qa lead", "qa manager",
            "selenium", "cypress", "playwright",
            "manual testing", "performance testing",
            "load testing", "stress testing",
        ],
    },
    "internships": {
        "name": "Internships",
        "icon": "graduation-cap",
        "keywords": [
            "intern", "internship", "trainee", "training program",
            "graduate program", "junior", "entry level", "entry-level",
            "fresh graduate", "fresh grad", "co-op",
            "apprentice", "apprenticeship",
            "working student", "student developer",
        ],
    },
}

# ─── API Keys ───────────────────────────────────────────────
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
FINDWORK_API_KEY = os.getenv("FINDWORK_API_KEY", "")
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY", "")
REED_API_KEY = os.getenv("REED_API_KEY", "")
MUSE_API_KEY = os.getenv("MUSE_API_KEY", "")

# ─── Database ───────────────────────────────────────────────
DATABASE_PATH = os.getenv("DATABASE_PATH", "jobs.db")
JOB_EXPIRY_DAYS = 5  # delete jobs older than this

# ─── Fetcher Settings ───────────────────────────────────────
FETCH_INTERVAL_MINUTES = 20
MAX_JOBS_PER_RUN = 200
REQUEST_TIMEOUT = 15

# ─── Pagination ─────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50

# ─── Geo-filtering ──────────────────────────────────────────
ALLOWED_ONSITE_COUNTRIES = {"egypt", "مصر", "saudi arabia", "saudi", "ksa", "السعودية"}

EGYPT_PATTERNS = {
    "egypt", "مصر", "cairo", "القاهرة", "alexandria", "الإسكندرية",
    "giza", "الجيزة", "minya", "المنيا", "mansoura", "المنصورة",
    "tanta", "طنطا", "aswan", "أسوان", "luxor", "الأقصر",
    "port said", "بورسعيد", "suez", "السويس", "ismailia", "الإسماعيلية",
    "fayoum", "الفيوم", "zagazig", "الزقازيق", "damanhur", "دمنهور",
    "beni suef", "بني سويف", "sohag", "سوهاج", "asyut", "أسيوط",
    "qena", "قنا", "hurghada", "الغردقة", "sharm el sheikh",
    "new cairo", "6th of october", "6 october", "smart village",
    "new capital", "العاصمة الإدارية", "nasr city", "مدينة نصر",
    "maadi", "المعادي", "heliopolis", "مصر الجديدة", "dokki", "الدقي",
    "mohandessin", "المهندسين",
}

SAUDI_PATTERNS = {
    "saudi arabia", "saudi", "ksa", "السعودية", "المملكة العربية السعودية",
    "riyadh", "الرياض", "jeddah", "جدة", "mecca", "مكة",
    "medina", "المدينة", "dammam", "الدمام", "khobar", "الخبر",
    "dhahran", "الظهران", "tabuk", "تبوك", "abha", "أبها",
    "taif", "الطائف", "jubail", "الجبيل", "yanbu", "ينبع",
    "neom", "نيوم", "qassim", "القصيم", "hail", "حائل",
    "jazan", "جازان", "najran", "نجران", "al kharj", "الخرج",
}

REMOTE_PATTERNS = {
    "remote", "anywhere", "worldwide", "work from home", "wfh",
    "distributed", "global", "fully remote", "100% remote",
    "remote-friendly", "location independent", "عن بعد",
}

# ─── Job Keywords ────────────────────────────────────────────
INCLUDE_KEYWORDS = [
    "software engineer", "software developer", "software development",
    "swe", "sde",
    "backend", "back-end", "back end", "server-side", "server side",
    "api developer", "api engineer",
    "frontend", "front-end", "front end", "ui developer", "ui engineer",
    "full-stack", "full stack", "fullstack",
    "devops", "dev ops", "dev-ops", "sre", "site reliability",
    "cloud engineer", "cloud developer", "cloud architect",
    "infrastructure engineer", "platform engineer",
    "kubernetes", "docker", "terraform",
    "aws engineer", "azure engineer", "gcp engineer",
    "qa engineer", "qa developer", "quality assurance",
    "test engineer", "sdet", "software tester",
    "automation engineer", "test automation",
    "qa analyst", "qa lead", "qa manager",
    "mobile developer", "mobile engineer", "mobile application",
    "ios developer", "ios engineer",
    "android developer", "android engineer",
    "flutter developer", "flutter engineer", "flutter",
    "react native developer", "react native engineer", "react native",
    "swift developer", "kotlin developer",
    "mobile app developer", "app developer",
    "web developer", "web engineer", "webmaster",
    "machine learning", "ml engineer", "ml developer",
    "ai engineer", "ai developer", "artificial intelligence",
    "deep learning", "nlp engineer", "computer vision",
    "data scientist", "data science", "data analyst", "data analytics",
    "data engineer", "etl developer", "data pipeline",
    "big data", "hadoop", "spark engineer",
    "security engineer", "appsec", "application security",
    "cybersecurity", "cyber security", "infosec",
    "penetration tester", "pen tester", "security analyst",
    "soc analyst", "security architect",
    "database administrator", "dba", "database developer", "database engineer",
    "sql developer", "postgresql", "mongodb",
    "blockchain developer", "blockchain engineer",
    "smart contract", "solidity developer",
    "web3 developer", "web3 engineer", "crypto developer",
    "game developer", "game engineer", "game programmer",
    "unity developer", "unreal developer", "game designer",
    "embedded developer", "embedded engineer", "embedded software",
    "iot developer", "iot engineer", "firmware developer", "firmware engineer",
    "systems engineer", "systems developer", "systems programmer",
    "kernel developer", "linux engineer", "os developer",
    "salesforce developer", "sap developer", "sap engineer",
    "erp developer", "crm developer", "dynamics developer", "odoo developer",
    "network engineer", "network administrator", "network architect",
    "python developer", "python engineer",
    "java developer", "java engineer",
    "javascript developer", "js developer",
    "typescript developer", "ts developer",
    "golang developer", "go developer", "go engineer",
    "rust developer", "rust engineer",
    "ruby developer", "ruby engineer", "rails developer",
    "php developer", "php engineer",
    "c# developer", ".net developer", "dotnet developer",
    "c++ developer", "cpp developer",
    "scala developer", "elixir developer",
    "node.js developer", "nodejs developer", "node developer",
    "react developer", "react engineer", "next.js developer",
    "angular developer", "vue developer", "vue.js developer",
    "django developer", "flask developer", "fastapi",
    "spring developer", "spring boot",
    "laravel developer", "symfony developer",
    "wordpress developer", "shopify developer",
    "tech lead", "technical lead", "engineering manager",
    "cto", "vp engineering", "head of engineering",
    "principal engineer", "staff engineer", "architect",
    "coding instructor", "programming instructor",
    "coding tutor", "programming tutor",
    "technical trainer", "coding mentor",
    "erp developer", "erp consultant", "erp engineer",
    "odoo developer", "odoo engineer", "odoo consultant", "odoo",
    "sap developer", "sap consultant", "sap engineer",
    "sap abap", "sap fiori", "sap hana", "sap basis",
    "salesforce developer", "salesforce engineer", "salesforce admin",
    "dynamics developer", "dynamics 365", "dynamics consultant",
    "oracle developer", "oracle ebs", "oracle apps", "oracle dba",
    "netsuite developer", "netsuite consultant",
    "crm developer", "crm engineer",
    "intern", "internship", "trainee",
    "graduate program", "training program",
    "co-op", "apprentice", "apprenticeship",
    "digital marketing", "digital marketer",
    "social media marketing", "social media manager", "social media specialist",
    "growth marketing", "growth hacker", "growth manager",
    "seo specialist", "seo manager", "seo analyst",
    "sem specialist", "sem manager",
    "ppc specialist", "ppc manager", "paid media",
    "content marketing", "content strategist", "content manager",
    "email marketing", "email specialist",
    "marketing automation", "marketing analyst",
    "performance marketing", "demand generation",
    "brand marketing", "brand manager",
    "community manager", "community specialist",
    "copywriter", "content writer", "content creator",
    "marketing manager", "marketing coordinator",
    "marketing specialist", "marketing director",
    "data engineer", "etl developer", "data pipeline",
    "data architect", "data platform",
    "big data engineer", "hadoop engineer", "spark engineer",
    "airflow", "dbt developer", "data warehouse",
    "snowflake developer", "redshift", "databricks",
    "data ops", "dataops", "analytics engineer",
    "application support", "app support",
    "application analyst", "application engineer",
    "technical support engineer", "it support engineer",
    "production support", "l2 support", "l3 support",
    "helpdesk engineer", "service desk",
    "incident management", "system support",
    "programmer", "developer", "engineer",
]

EXCLUDE_KEYWORDS = [
    "graphic design", "ui/ux design", "ux design", "ux researcher",
    "product design", "visual design", "brand design", "interior design",
    "recruiter", "talent acquisition", "hr manager", "human resources",
    "customer support", "customer service", "customer success",
    "project manager", "program manager", "scrum master",
    "product manager", "product owner",
    "financial analyst", "accountant", "bookkeeper",
    "office manager", "administrative",
    "supply chain", "logistics",
    "sales representative", "sales executive", "account executive",
    "real estate agent", "insurance agent",
    "mechanical engineer", "electrical engineer", "civil engineer",
    "chemical engineer", "structural engineer",
    "hardware engineer", "pcb",
    "medical coder", "billing coder", "clinical",
    "nurse", "physician", "pharmacist",
    "dental", "veterinary",
]

# ─── Emoji Map ───────────────────────────────────────────────
EMOJI_MAP = {
    "backend": "⚙️", "back-end": "⚙️",
    "frontend": "🎨", "front-end": "🎨",
    "full-stack": "🔄", "fullstack": "🔄",
    "devops": "🚀", "sre": "🚀", "cloud": "☁️",
    "qa": "🧪", "test": "🧪",
    "mobile": "📱", "ios": "🍎", "android": "🤖",
    "flutter": "🦋", "react native": "📱",
    "python": "🐍", "java": "☕",
    "javascript": "🟨", "typescript": "🔷",
    "react": "⚛️", "node": "🟩",
    "golang": "🐹", "rust": "🦀", "ruby": "💎", "php": "🐘",
    ".net": "🟣", "c#": "🟣", "c++": "🔵",
    "swift": "🍎", "kotlin": "🟠",
    "data engineer": "📊", "data scien": "📊",
    "machine learning": "🤖", "ml ": "🤖", "ai ": "🤖",
    "deep learning": "🧠",
    "blockchain": "⛓️", "web3": "⛓️", "solidity": "⛓️",
    "game dev": "🎮", "unity": "🎮", "unreal": "🎮",
    "security": "🔒", "cyber": "🔒",
    "embedded": "🔌", "iot": "🔌",
    "database": "🗄️", "dba": "🗄️", "sql": "🗄️",
    "senior": "👨‍💻", "junior": "🌱", "lead": "⭐",
    "intern": "🎓", "architect": "🏗️",
    "remote": "🌍",
    "egypt": "🇪🇬", "مصر": "🇪🇬", "cairo": "🇪🇬",
    "saudi": "🇸🇦", "riyadh": "🇸🇦", "jeddah": "🇸🇦",
}

DEFAULT_EMOJI = "💻"

SOURCE_DISPLAY = {
    "remotive": "Remotive",
    "himalayas": "Himalayas",
    "jobicy": "Jobicy",
    "remoteok": "RemoteOK",
    "arbeitnow": "Arbeitnow",
    "wwr": "We Work Remotely",
    "workingnomads": "Working Nomads",
    "jsearch": None,
    "linkedin": "LinkedIn",
    "adzuna": "Adzuna",
    "themuse": "The Muse",
    "findwork": "Findwork",
    "jooble": "Jooble",
    "reed": "Reed",
    "usajobs": "USAJobs",
}
