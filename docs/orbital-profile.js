(() => {
  const origin = "https://raw.githubusercontent.com/Harishik/Harishik/main/";
  const pins = document.querySelector("#orbital-pins-list");
  const activity = document.querySelector("#orbital-activity-list");
  const stats = document.querySelector("#orbital-calendar-stats");
  const motion = document.querySelector("#motion");

  function currentMotion() {
    document.body.dataset.motion = String(motion.textContent === "Pause motion");
  }

  function link(title, destination) {
    const anchor = document.createElement("a");
    const url = new URL(destination);
    if (url.origin !== "https://github.com" && url.origin !== "https://gist.github.com") {
      throw new Error("Unexpected GitHub link");
    }
    anchor.href = url.href;
    anchor.textContent = title;
    return anchor;
  }

  function item(title, url, description, date) {
    const li = document.createElement("li");
    li.append(link(title, url));
    const summary = document.createElement("span");
    summary.textContent = description;
    li.append(summary);
    if (date) {
      const time = document.createElement("time");
      time.dateTime = date;
      time.textContent = date.slice(0,10);
      li.append(time);
    }
    return li;
  }

  function show(snapshot) {
    const pinRows = snapshot.profile.pins.map(pin => item(pin.title, pin.url, pin.summary || "Public pin"));
    const activityRows = (snapshot.activity || []).map(event => item(event.repo,event.url,event.label,event.at));
    pins.replaceChildren(...pinRows);
    activity.replaceChildren(...activityRows);
    if (!pinRows.length) pins.textContent = "No public pins are set.";
    if (!activityRows.length) activity.textContent = "No recent public repository events in the available window.";
    const count = snapshot.calendar.reduce((sum,day) => sum + day[3],0);
    const active = snapshot.calendar.filter(day => day[2]>0).length;
    stats.textContent = `${snapshot.dates[0]} to ${snapshot.dates[1]} · ${active} active days · ${count} public calendar contributions`;
  }

  new MutationObserver(currentMotion).observe(motion,{childList:true,subtree:true});
  currentMotion();
  show(JSON.parse(document.querySelector("#public-snapshot").textContent));
  fetch(origin + "profile.json", {cache:"no-cache"})
    .then(response => response.ok ? response.json() : Promise.reject(new Error("Public snapshot unavailable")))
    .then(snapshot => { if (Array.isArray(snapshot.activity)) show(snapshot); })
    .catch(() => {});
})();
