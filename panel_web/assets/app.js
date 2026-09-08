const views = [...document.querySelectorAll("[data-view]")];
const links = [...document.querySelectorAll("[data-page]")];
const title = document.querySelector("#pageTitle");
const sidebar = document.querySelector(".sidebar");
const titles = Object.fromEntries(links.map(a => [a.dataset.page, a.textContent.trim()]));

function showPage(name){
  if(!titles[name]) name="dashboard";
  views.forEach(v => v.hidden = v.dataset.view !== name);
  links.forEach(a => a.classList.toggle("active", a.dataset.page === name));
  title.textContent = titles[name];
  document.title = `v-bot • ${titles[name]}`;
  history.replaceState(null, "", `#${name}`);
  sidebar?.classList.remove("open");
}
links.forEach(a => a.addEventListener("click", e => { e.preventDefault(); showPage(a.dataset.page); }));
document.querySelector("#mobileToggle")?.addEventListener("click", () => sidebar.classList.toggle("open"));
showPage(location.hash.slice(1) || "dashboard");
