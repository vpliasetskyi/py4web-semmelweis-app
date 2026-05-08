/**
 * renderClinicChart
 * Draws a dual-line chart comparing death proportions for Clinic 1 vs Clinic 2.
 *
 * @param {string} canvasId - the id attribute of the <canvas> element
 * @param {object} data     - { labels: [year,...], clinic1: [...], clinic2: [...] }
 */
function renderClinicChart(canvasId, data) {
  const el = document.getElementById(canvasId);
  if (!el || !data || data.empty) return;  // silent guard — no data yet

  new Chart(el, {
    type: "line",
    data: {
      labels: data.labels,   // x-axis: years
      datasets: [
        {
          label: "Clinic 1",
          data: data.clinic1,
          borderColor: "#ef4444",                    // Tailwind red-500
          backgroundColor: "rgba(239,68,68,0.1)",    // transparent fill
          pointRadius: 5,
          tension: 0.3,   // slight curve on lines
          fill: true,
        },
        {
          label: "Clinic 2",
          data: data.clinic2,
          borderColor: "#22c55e",                    // Tailwind green-500
          backgroundColor: "rgba(34,197,94,0.1)",
          pointRadius: 5,
          tension: 0.3,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,  // allows the chart to fill the parent div's height
      plugins: { legend: { position: "top" } },
      scales: {
        y: {
          title: { display: true, text: "Proportion of deaths" },
          beginAtZero: true,
        },
        x: { title: { display: true, text: "Year" } },
      },
    },
  });
}

/**
 * renderMonthlyChart
 * Draws two connected line segments: one red (before June 1847) and one green
 * (after), on a single shared x-axis. Nulls pad the inactive segment so
 * Chart.js draws them as separate non-connected lines.
 *
 * @param {string} canvasId
 * @param {object} data - { labelsBefore, before, labelsAfter, after }
 */
function renderMonthlyChart(canvasId, data) {
  const el = document.getElementById(canvasId);
  if (!el || !data || data.empty) return;

  // Merge both label arrays into a single x-axis.
  const allLabels = [...data.labelsBefore, ...data.labelsAfter];

  // Pad each dataset with nulls on the side where it has no data.
  // spanGaps: false means Chart.js will NOT connect across nulls — the gap
  // between the two coloured segments is intentional.
  const beforePadded = [
    ...data.before,
    ...new Array(data.labelsAfter.length).fill(null),
  ];
  const afterPadded = [
    ...new Array(data.labelsBefore.length).fill(null),
    ...data.after,
  ];

  new Chart(el, {
    type: "line",
    data: {
      labels: allLabels,
      datasets: [
        {
          label: "Before handwashing",
          data: beforePadded,
          borderColor: "#ef4444",
          backgroundColor: "rgba(239,68,68,0.08)",
          pointRadius: 3,
          tension: 0.2,
          spanGaps: false,   // do not bridge the null gap
          fill: true,
        },
        {
          label: "After handwashing",
          data: afterPadded,
          borderColor: "#22c55e",
          backgroundColor: "rgba(34,197,94,0.08)",
          pointRadius: 3,
          tension: 0.2,
          spanGaps: false,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } },
      scales: {
        y: {
          title: { display: true, text: "Proportion of deaths" },
          beginAtZero: true,
        },
        x: {
          ticks: { maxTicksLimit: 14, maxRotation: 45 },
          title: { display: true, text: "Date" },
        },
      },
    },
  });
}

/**
 * renderBootstrapHistogram
 * Draws a bar chart (histogram) of the bootstrap distribution.
 * Bars outside the 95 % CI are coloured red; bars inside are blue.
 *
 * @param {string} canvasId
 * @param {object} data - { labels, counts, ci_lower, ci_upper }
 */
function renderBootstrapHistogram(canvasId, data) {
  const el = document.getElementById(canvasId);
  if (!el || !data || data.empty) return;

  new Chart(el, {
    type: "bar",
    data: {
      labels: data.labels,
      datasets: [
        {
          label: "Frequency",
          data: data.counts,
          // Colour each bar based on whether it falls inside the CI.
          backgroundColor: data.labels.map((v) => {
            if (v < data.ci_lower || v > data.ci_upper)
              return "rgba(239,68,68,0.4)";    // red: outside CI
            return "rgba(59,130,246,0.6)";     // blue: inside CI
          }),
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            // Show the bin centre value in the tooltip header.
            title: (items) => `Diff ≈ ${items[0].label}`,
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: "Mean difference in proportion deaths" },
          ticks: { maxTicksLimit: 10 },
        },
        y: { title: { display: true, text: "Count" } },
      },
    },
  });
}