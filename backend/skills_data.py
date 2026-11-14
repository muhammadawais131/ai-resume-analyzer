"""Static knowledge used by the rule-based ATS engine."""

# Hard skills / tools across common domains. Multi-word entries are matched as phrases.
HARD_SKILLS = {
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "php", "ruby", "golang", "rust",
    "swift", "kotlin", "scala", "perl", "matlab", "dart", "objective-c", "sql", "nosql", "bash",
    "powershell", "vba", "solidity",
    # Web / frameworks
    "html", "css", "sass", "tailwind", "bootstrap", "react", "react native", "next.js", "vue",
    "nuxt", "angular", "svelte", "jquery", "node.js", "express.js", "nestjs", "django", "flask",
    "fastapi", "spring", "spring boot", "laravel", "symfony", "codeigniter", "rails", ".net",
    "asp.net", "flutter", "redux", "graphql", "rest api", "restful", "websocket", "microservices",
    "oauth", "jwt", "webpack", "vite",
    # Data / AI
    "machine learning", "deep learning", "nlp", "computer vision", "data analysis",
    "data science", "data visualization", "data engineering", "statistics", "pandas", "numpy",
    "scikit-learn", "tensorflow", "pytorch", "keras", "opencv", "llm", "generative ai",
    "langchain", "spark", "hadoop", "airflow", "kafka", "etl", "power bi", "tableau", "looker",
    "excel", "google sheets", "a/b testing", "big data", "snowflake", "databricks", "dbt",
    # Databases
    "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle", "sql server", "mariadb",
    "elasticsearch", "dynamodb", "firebase", "supabase", "cassandra",
    # Cloud / DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "ci/cd", "nginx", "apache", "linux", "unix",
    "serverless", "lambda", "ec2", "s3", "devops", "prometheus", "grafana",
    # Tools
    "git", "github", "gitlab", "bitbucket", "jira", "confluence", "postman", "swagger", "figma",
    "adobe xd", "photoshop", "illustrator", "canva", "notion", "trello", "asana", "slack",
    "salesforce", "hubspot", "sap", "quickbooks", "zendesk", "wordpress", "shopify",
    # Testing / QA
    "unit testing", "integration testing", "test automation", "selenium", "cypress", "jest",
    "pytest", "phpunit", "playwright", "tdd",
    # Methods / business
    "agile", "scrum", "kanban", "project management", "product management", "seo", "sem",
    "google analytics", "digital marketing", "content marketing", "social media marketing",
    "email marketing", "copywriting", "crm", "erp", "budgeting", "forecasting",
    "financial analysis", "financial modeling", "accounting", "bookkeeping", "payroll",
    "inventory management", "supply chain", "logistics", "procurement", "customer service",
    "customer support", "sales", "lead generation", "b2b", "b2c", "recruiting", "onboarding",
    "ux design", "ui design", "user research", "wireframing", "prototyping",
    "cybersecurity", "penetration testing", "networking", "tcp/ip", "itil",
    # Certifications
    "pmp", "cpa", "cfa", "aws certified", "ccna", "comptia", "six sigma", "scrum master",
}

SOFT_SKILLS = {
    "leadership", "communication", "teamwork", "collaboration", "problem solving",
    "problem-solving", "critical thinking", "time management", "adaptability", "creativity",
    "attention to detail", "analytical", "mentoring", "negotiation", "presentation",
    "stakeholder management", "decision making", "organization", "multitasking",
    "interpersonal", "customer focus", "ownership", "self-motivated", "conflict resolution",
}

# Map common variants to a canonical skill name.
SKILL_ALIASES = {
    "js": "javascript", "es6": "javascript", "ts": "typescript",
    "reactjs": "react", "react.js": "react", "vuejs": "vue", "vue.js": "vue",
    "nextjs": "next.js", "angularjs": "angular",
    "node": "node.js", "nodejs": "node.js", "expressjs": "express.js", "express": "express.js",
    "postgres": "postgresql", "mongo": "mongodb", "mssql": "sql server",
    "k8s": "kubernetes", "golang": "golang", "go lang": "golang",
    "rest apis": "rest api", "restful api": "rest api", "restful apis": "rest api",
    "sklearn": "scikit-learn", "ml": "machine learning", "ai/ml": "machine learning",
    "gen ai": "generative ai", "genai": "generative ai", "large language models": "llm",
    "powerbi": "power bi", "ms excel": "excel", "microsoft excel": "excel",
    "google cloud platform": "gcp", "amazon web services": "aws", "ci cd": "ci/cd",
    "html5": "html", "css3": "css", "dotnet": ".net",
}

# Strong action verbs (past + present forms) for bullet openings.
ACTION_VERBS = {
    "achieved", "accelerated", "administered", "analyzed", "architected", "automated", "built",
    "boosted", "championed", "coached", "collaborated", "configured", "consolidated",
    "coordinated", "created", "cut", "debugged", "delivered", "deployed", "designed",
    "developed", "devised", "directed", "drove", "earned", "eliminated", "enabled",
    "engineered", "enhanced", "established", "evaluated", "executed", "expanded", "facilitated",
    "founded", "generated", "grew", "guided", "headed", "identified", "implemented", "improved",
    "increased", "initiated", "innovated", "integrated", "introduced", "launched", "led",
    "maintained", "managed", "maximized", "mentored", "migrated", "minimized", "modernized",
    "negotiated", "optimized", "orchestrated", "organized", "overhauled", "oversaw", "partnered",
    "pioneered", "planned", "produced", "programmed", "published", "realized", "rebuilt",
    "recruited", "redesigned", "reduced", "refactored", "resolved", "restructured", "revamped",
    "saved", "scaled", "secured", "simplified", "spearheaded", "streamlined", "strengthened",
    "supervised", "tested", "trained", "transformed", "tripled", "doubled", "upgraded", "won",
    "wrote", "conducted", "prepared", "handled", "processed", "served", "supported", "authored",
    "build", "design", "develop", "lead", "manage", "create", "implement", "deliver", "drive",
    "own", "maintain", "optimize", "analyze", "coordinate", "train", "mentor",
}

WEAK_PHRASES = [
    "responsible for", "worked on", "helped with", "helped to", "assisted with", "assisted in",
    "duties included", "tasked with", "involved in", "participated in", "in charge of",
    "worked with", "was part of", "tried to",
]

BUZZWORDS = [
    "hard worker", "hardworking", "team player", "go-getter", "think outside the box",
    "synergy", "results-driven", "self-starter", "detail-oriented", "dynamic", "passionate",
    "motivated individual", "go getter", "best of breed", "rockstar", "ninja", "guru",
    "proven track record", "fast learner", "quick learner",
]

# Section name -> header aliases (matched against short, standalone lines).
SECTION_ALIASES = {
    "summary": ["summary", "professional summary", "profile", "about me", "objective",
                "career objective", "professional profile", "career summary", "about"],
    "experience": ["experience", "work experience", "professional experience", "employment",
                   "employment history", "work history", "career history", "internships",
                   "internship", "relevant experience"],
    "education": ["education", "academic background", "academics", "qualifications",
                  "academic qualifications", "education & training", "education and training"],
    "skills": ["skills", "technical skills", "core skills", "key skills", "core competencies",
               "competencies", "skills & tools", "tools", "technologies", "tech stack",
               "skills and abilities", "areas of expertise", "expertise"],
    "projects": ["projects", "personal projects", "key projects", "academic projects",
                 "selected projects", "portfolio"],
    "certifications": ["certifications", "certificates", "licenses", "courses",
                       "licenses & certifications", "training", "certification"],
    "achievements": ["achievements", "awards", "honors", "accomplishments",
                     "awards & honors"],
}
