window.portfolioData = {
  profile: {
    name: "Changxin Shi",
    role: "Data Analyst / Data Scientist",
    tagline:
      "UC Berkeley MS Analytics candidate translating operations, finance, healthcare, social media, and product data into dashboards, experiments, machine learning models, and decision-ready recommendations.",
    location: "Berkeley, CA",
    phone: "5105423383",
    email: "cxshi@berkeley.edu",
    linkedin: "https://www.linkedin.com/in/changxin-shi-b4732937a/",
    github: "https://github.com/HebeiZywoo?tab=repositories",
    resume: "assets/Changxin_Shi_Resume_DS.pdf",
    resumeDA: "assets/Changxin_Shi_Resume_DA.pdf",
    resumeDS: "assets/Changxin_Shi_Resume_DS.pdf",
  },
  proofPoints: [
    { value: "1+ yr", label: "Applied DA/DS experience" },
    { value: "4.00", label: "Berkeley MS Analytics GPA" },
    { value: "30%", label: "Reporting time reduction" },
    { value: "115.7%", label: "Projected campaign ROI" },
  ],
  education: [
    {
      school: "University of California-Berkeley",
      degree: "Master of Science in Analytics",
      dates: "Aug 2025 - Aug 2026",
      detail: "All coursework completed by May 2026, GPA 4.00/4.00",
    },
    {
      school: "Kean University",
      degree: "Bachelor of Science in Finance",
      dates: "Aug 2021 - May 2025",
      detail: "Minor in Economics & Math, GPA 3.90/4.00",
    },
  ],
  skills: [
    {
      group: "Programming & Data",
      items: ["Python", "SQL", "R", "PySpark", "pandas", "NumPy", "SciPy", "Git"],
    },
    {
      group: "Analytics & Experimentation",
      items: [
        "A/B testing",
        "Causal inference",
        "KPI reporting",
        "Statistical analysis",
        "Customer segmentation",
        "Cohort analysis",
      ],
    },
    {
      group: "Machine Learning",
      items: [
        "Feature engineering",
        "Random Forest",
        "XGBoost",
        "Time series",
        "Predictive modeling",
        "Model evaluation",
      ],
    },
    {
      group: "Platforms & BI",
      items: [
        "Tableau",
        "Power BI",
        "Databricks",
        "AWS",
        "Snowflake",
        "DuckDB",
        "Streamlit",
        "Excel",
      ],
    },
  ],
  experience: [
    {
      title: "Data Analyst Intern",
      company: "Gala Circle Inc.",
      location: "San Jose, CA",
      dates: "May 2026 - Present",
      summary:
        "Operational and merchant analytics for restaurant partners, focused on KPI validation, segmentation, and expansion planning.",
      bullets: [
        "Validated operational and financial metrics across 30+ restaurant merchants, creating analysis-ready performance datasets.",
        "Standardized merchant KPI logic and QA checks for revenue, order volume, service, and conversion metrics.",
        "Prioritized merchants into 3-5 tiers by scale, operations, and service needs to guide partner strategy and expansion.",
        "Triangulated structured data with 10+ merchant interviews to identify demand drivers, bottlenecks, and growth opportunities.",
      ],
    },
    {
      title: "Data Analyst",
      company: "University of California-Berkeley",
      location: "Berkeley, CA",
      dates: "Jan 2026 - Present",
      summary:
        "Academic service analytics across circulation, digital access, and space utilization data for library operations.",
      bullets: [
        "Automated cleaning and integration of circulation, digital access, and space utilization data using Python and SQL CTEs.",
        "Delivered a Tableau dashboard tracking 10+ KPIs across 12 library branches, reducing stakeholder reporting time by 30%.",
        "Diagnosed usage patterns, demand trends, and peak periods across departments to support evidence-based resource allocation.",
        "Translated findings into service optimization recommendations for librarians, IT staff, and administrative stakeholders.",
      ],
    },
    {
      title: "Operation Analyst Intern",
      company: "Xiaochuan Technology",
      location: "",
      dates: "Jun 2025 - Aug 2025",
      summary:
        "Product operations and social engagement analytics for U.S. social content, recommendations, and UGC growth.",
      bullets: [
        "Segmented 10,000+ U.S. social posts with MySQL and clustering across tags, comment types, and engagement metrics.",
        "Ran A/B tests for recommendation changes, lifting top comments 22%, daily UGC comments 2,000+, and comment rate 7.3%.",
        "Developed Tableau dashboards from MySQL outputs to monitor UGC engagement trends for product and operations stakeholders.",
        "Partnered with product and engineering teams to deploy scalable recommendation optimizations in production.",
      ],
    },
    {
      title: "Data Analyst Intern",
      company: "Dongxing Securities",
      location: "",
      dates: "May 2024 - Aug 2024",
      summary:
        "Financial modeling and quantitative strategy analysis for CSI 500 multi-factor performance.",
      bullets: [
        "Analyzed financial data in Python and built 6+ composite factors to evaluate CSI 500 strategy performance.",
        "Built Random Forest, LASSO, and ARIMA models for backtesting classification, regression, and time-series strategies.",
        "Improved multi-factor model performance by +1.52% annualized alpha, +0.09 IR, and -1.05% relative drawdown.",
        "Collaborated with traders and strategists to gather requirements, explore feasible factors, and refine data-driven investment strategy.",
      ],
    },
    {
      title: "Data Analyst Intern",
      company: "Industrial and Commercial Bank of China",
      location: "",
      dates: "Nov 2023 - Jan 2024",
      summary:
        "Portfolio analysis and reporting automation across client accounts, transaction data, and market data.",
      bullets: [
        "Used SQL to extract, clean, and transform transaction and market data for portfolio analysis across 15+ client accounts.",
        "Performed return attribution and volatility analysis to uncover allocation inefficiencies, improving portfolio risk-adjusted return by 2.3%.",
        "Standardized validation and reporting templates, reducing reporting discrepancies by 20% and improving portfolio analysis accuracy.",
      ],
    },
    {
      title: "Management Consultant Intern",
      company: "IQVIA Solutions Enterprise",
      location: "",
      dates: "Jun 2023 - Aug 2023",
      summary:
        "Healthcare market sizing and executive decision support for China's HPV vaccine market.",
      bullets: [
        "Analyzed 12-city healthcare data on providers, demographics, and pricing to size China's HPV vaccine market.",
        "Built SQL-based analysis and ETL pipelines, combining quantitative market modeling with insights from 20+ physicians and 10+ pharma leaders.",
        "Designed 5+ interview guides, capturing physician and pharma-leader insights for market-sizing assumptions.",
        "Created deliverables supporting a pharma IPO strategy through statistical analysis and visual storytelling in Tableau.",
      ],
    },
  ],
  projects: [
    {
      title: "Product Experimentation & Causal Impact Platform",
      type: "Product DS / Experimentation",
      image: "",
      summary:
        "An experimentation and causal inference workspace for evaluating product launches across users, activity events, marketplace orders, and post-launch health signals.",
      highlights: [
        "Built an experimentation analytics workspace to evaluate product changes across 8K users, 784K activity events, and 16.8K marketplace orders.",
        "Compared A/B testing, propensity score matching, and difference-in-differences methods to estimate conversion, revenue, and marketplace impact.",
        "Measured an 11.8pp conversion lift and translated statistical results into launch recommendations, risk flags, and follow-up analysis priorities.",
        "Added post-launch diagnostics for review quality, delivery delay, revenue movement, and feature drift to support ongoing product monitoring.",
      ],
      metrics: ["8K users", "784K events", "16.8K orders", "11.8pp lift"],
      stack: ["Python", "SQL", "Causal inference", "A/B testing", "Propensity score matching"],
      links: [
        {
          label: "GitHub",
          href: "https://github.com/HebeiZywoo/Product-Experimentation-Platform",
        },
      ],
    },
    {
      title: "AI Customer Intelligence & Campaign ROI Platform",
      type: "Customer Analytics / Machine Learning",
      image: "../reports/dashboard_home.png",
      summary:
        "A Python, DuckDB, and Streamlit platform for ecommerce segmentation, repeat-purchase prediction, campaign holdout analysis, and ROI recommendations.",
      highlights: [
        "Built a customer intelligence dashboard to evaluate customer segments, repeat purchase behavior, campaign lift, and revenue impact.",
        "Created RFM, lifecycle, channel cohort, and campaign tables for targeted-offer recommendations.",
        "Implemented a DuckDB SQL reporting layer for cohort summaries, holdout analysis, and reusable campaign KPI views.",
        "Benchmarked three repeat-purchase models; selected Random Forest with 0.709 ROC AUC and linked 7.2pp campaign lift to $2.0K net profit.",
      ],
      metrics: ["0.709 ROC AUC", "7.2pp lift", "$2.0K net profit", "115.7% ROI"],
      stack: ["Python", "DuckDB", "SQL", "scikit-learn", "Streamlit", "Tableau-style dashboarding"],
      links: [
        {
          label: "GitHub",
          href: "https://github.com/HebeiZywoo/customer-intelligence-with-AI",
        },
        { label: "Case study", href: "../docs/case_study.md" },
        { label: "Model card", href: "../docs/model_card.md" },
      ],
    },
  ],
  leadership: [
    {
      title: "President",
      organization: "Association for Career and Innovation",
      dates: "Nov 2023 - May 2025",
      summary:
        "Led a career and innovation-focused student organization connecting students, recruiters, executives, professors, and corporate partners.",
      bullets: [
        "Supported 100+ students in career development by coordinating recruiter outreach, career fairs, employer information sessions, and school-based hiring events.",
        "Invited corporate executives and well-known professors to campus for career talks, industry lectures, and student-facing professional development programs.",
        "Expanded university-industry collaboration by securing partnerships with 5+ companies, including fixed recruiter relationships, campus presence, and business cooperation opportunities.",
        "Partnered with companies to host multiple business competitions and innovation events, including Marketing Competition and AI Hackathon programs.",
      ],
    },
  ],
};
