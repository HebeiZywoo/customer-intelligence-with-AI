const data = window.portfolioData;

const escapeHtml = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const setText = (selector, value) => {
  document.querySelectorAll(selector).forEach((node) => {
    node.textContent = value;
  });
};

const setLink = (key, href) => {
  document.querySelectorAll(`[data-link="${key}"]`).forEach((node) => {
    if (key === "email") {
      node.href = `mailto:${href}`;
      return;
    }
    node.href = href;
  });
};

const listItems = (items) => items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");

const renderEducation = () => {
  document.getElementById("education-list").innerHTML = data.education
    .map(
      (entry) => `
        <article class="timeline-card education-card">
          <h3>${escapeHtml(entry.school)}</h3>
          <div class="timeline-meta">${escapeHtml(entry.degree)} · ${escapeHtml(entry.dates)}</div>
          <p>${escapeHtml(entry.detail)}</p>
        </article>
      `,
    )
    .join("");
};

const renderProofPoints = () => {
  document.getElementById("proof-points").innerHTML = data.proofPoints
    .map(
      (point) => `
        <article class="proof-item">
          <span class="proof-value">${escapeHtml(point.value)}</span>
          <span class="proof-label">${escapeHtml(point.label)}</span>
        </article>
      `,
    )
    .join("");
};

const renderSkills = () => {
  document.getElementById("skills-grid").innerHTML = data.skills
    .map(
      (skill) => `
        <article class="skill-card">
          <h3>${escapeHtml(skill.group)}</h3>
          <ul>${listItems(skill.items)}</ul>
        </article>
      `,
    )
    .join("");
};

const renderTimeline = (targetId, entries) => {
  document.getElementById(targetId).innerHTML = entries
    .map(
      (entry) => `
        <article class="timeline-card">
          <h3>${escapeHtml(entry.title)}</h3>
          <div class="timeline-meta">${escapeHtml(entry.company || entry.organization)}${entry.location ? ` · ${escapeHtml(entry.location)}` : ""} · ${escapeHtml(entry.dates)}</div>
          <p>${escapeHtml(entry.summary)}</p>
          <ul>${listItems(entry.bullets)}</ul>
        </article>
      `,
    )
    .join("");
};

const renderProjects = () => {
  document.getElementById("project-list").innerHTML = data.projects
    .map(
      (project) => `
        <article class="project-card">
          <div class="project-visual">
            ${
              project.image
                ? `<img src="${escapeHtml(project.image)}" alt="${escapeHtml(project.title)} dashboard screenshot" />`
                : `<div class="project-visual-panel">
                    <span>${escapeHtml(project.type)}</span>
                    <strong>${escapeHtml(project.metrics[0])}</strong>
                    <p>${escapeHtml(project.metrics.slice(1).join(" / "))}</p>
                  </div>`
            }
          </div>
          <div class="project-content">
            <p class="project-type">${escapeHtml(project.type)}</p>
            <h3>${escapeHtml(project.title)}</h3>
            <p>${escapeHtml(project.summary)}</p>
            <ul>${listItems(project.highlights)}</ul>
            <div class="metric-row">
              ${project.metrics.map((metric) => `<span class="metric-pill">${escapeHtml(metric)}</span>`).join("")}
            </div>
            <div class="tag-row">
              ${project.stack.map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join("")}
            </div>
            <div class="project-links">
              ${project.links
                .map((link) => `<a href="${escapeHtml(link.href)}">${escapeHtml(link.label)}</a>`)
                .join("")}
            </div>
          </div>
        </article>
      `,
    )
    .join("");
};

const setupResumeModal = () => {
  const modal = document.getElementById("resume-modal");
  const title = document.getElementById("resume-title");
  const image = document.getElementById("resume-image");
  const download = document.getElementById("resume-download");
  const resumeAssets = {
    da: {
      title: "Changxin Shi - Data Analyst Resume",
      pdf: data.profile.resumeDA,
      image: "assets/resume-previews/Changxin_Shi_Resume_DA.pdf.png",
    },
    ds: {
      title: "Changxin Shi - Data Scientist Resume",
      pdf: data.profile.resumeDS,
      image: "assets/resume-previews/Changxin_Shi_Resume_DS.pdf.png",
    },
  };

  const close = () => {
    modal.hidden = true;
    document.body.classList.remove("modal-open");
  };

  const open = (type) => {
    const resume = resumeAssets[type] || resumeAssets.ds;
    title.textContent = resume.title;
    image.src = resume.image;
    image.alt = `${resume.title} preview`;
    download.href = resume.pdf;
    modal.hidden = false;
    document.body.classList.add("modal-open");
  };

  document.querySelectorAll("[data-resume]").forEach((button) => {
    button.addEventListener("click", () => open(button.dataset.resume));
  });

  document.querySelectorAll("[data-resume-close]").forEach((button) => {
    button.addEventListener("click", close);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hidden) {
      close();
    }
  });
};

const init = () => {
  document.title = `${data.profile.name} | ${data.profile.role}`;
  setText('[data-field="name"]', data.profile.name);
  setText('[data-field="role"]', data.profile.role);
  setText('[data-field="tagline"]', data.profile.tagline);
  setText('[data-field="location"]', data.profile.location);
  setText('[data-field="email"]', data.profile.email);
  setText('[data-field="phone"]', data.profile.phone);
  setLink("email", data.profile.email);
  setLink("linkedin", data.profile.linkedin);
  setLink("github", data.profile.github);
  setLink("resume", data.profile.resume);
  setLink("resumeDA", data.profile.resumeDA);
  setLink("resumeDS", data.profile.resumeDS);
  renderProofPoints();
  renderSkills();
  renderEducation();
  renderTimeline("experience-list", data.experience);
  renderProjects();
  renderTimeline("leadership-list", data.leadership);
  setupResumeModal();
};

init();
