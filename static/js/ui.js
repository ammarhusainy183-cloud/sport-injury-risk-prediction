// =========================================================
// GLOBAL CHART REFERENCES
// =========================================================

let riskHistoryChartInstance = null;
let exercisesChartInstance = null;
let trainingIntensityChartInstance = null;


// =========================================================
// AUTHENTICATION UI
// =========================================================

document.addEventListener("DOMContentLoaded", () => {
  window.switchAuthTab = function (tab) {
    const forms = document.querySelectorAll('[id$="-form"]');

    forms.forEach((element) => {
      element.classList.remove("active");
      element.classList.add("hidden");
    });

    document
      .querySelectorAll(".tab-button")
      .forEach((button) => button.classList.remove("active"));

    if (tab === "login") {
      const loginForm = document.getElementById("login-form");

      if (loginForm) {
        loginForm.classList.remove("hidden");
        loginForm.classList.add("active");
      }

      const loginButton = document.querySelector(
        '[onclick="switchAuthTab(\'login\')"]'
      );

      if (loginButton) {
        loginButton.classList.add("active");
      }
    }

    if (tab === "register") {
      const registerForm = document.getElementById("register-form");

      if (registerForm) {
        registerForm.classList.remove("hidden");
        registerForm.classList.add("active");
      }

      const registerButton = document.querySelector(
        '[onclick="switchAuthTab(\'register\')"]'
      );

      if (registerButton) {
        registerButton.classList.add("active");
      }
    }

    if (tab === "forgot-password") {
      const forgotForm = document.getElementById(
        "forgot-password-form"
      );

      if (forgotForm) {
        forgotForm.classList.remove("hidden");
        forgotForm.classList.add("active");
      }
    }

    if (tab === "reset-password") {
      const resetForm = document.getElementById(
        "reset-password-form"
      );

      if (resetForm) {
        resetForm.classList.remove("hidden");
        resetForm.classList.add("active");
      }
    }
  };

  if (
    document.getElementById("login-form") &&
    document.getElementById("register-form")
  ) {
    window.switchAuthTab("login");
  }

  document
    .querySelectorAll("input[required], textarea[required], select[required]")
    .forEach((input) => {
      input.addEventListener("invalid", () => {
        input.style.outline =
          "2px solid rgba(255, 122, 24, 0.35)";

        setTimeout(() => {
          input.style.outline = "";
        }, 1400);
      });
    });

  document.querySelectorAll(".social-btn").forEach((button) => {
    button.addEventListener("click", () => {
      alert(
        "Social login placeholder: " +
        button.textContent.trim()
      );
    });
  });

  initializeBackgroundSlideshow();
});


// =========================================================
// BACKGROUND SLIDESHOW
// =========================================================

function initializeBackgroundSlideshow() {
  const backgroundImages = [
    "/static/img/backgrounds/cr7.png",
    "/static/img/backgrounds/Modric.jpg",
    "/static/img/backgrounds/n.kante.jpg",
    "/static/img/backgrounds/neymar.jpg"
  ];

  const slides = document.querySelectorAll(
    ".background-slide"
  );

  if (slides.length < 2) {
    return;
  }

  if (backgroundImages.length === 0) {
    console.error("No background images were provided.");
    return;
  }

  let currentImageIndex = 0;
  let activeSlideIndex = 0;

  slides[0].style.backgroundImage =
    `url("${backgroundImages[0]}")`;

  slides[1].style.backgroundImage =
    `url("${backgroundImages[1 % backgroundImages.length]}")`;

  function changeBackground() {
    const currentSlide = slides[activeSlideIndex];

    const nextSlideIndex =
      activeSlideIndex === 0 ? 1 : 0;

    const nextSlide = slides[nextSlideIndex];

    currentImageIndex =
      (currentImageIndex + 1) %
      backgroundImages.length;

    nextSlide.style.transition = "none";
    nextSlide.style.transform = "translateX(100%)";
    nextSlide.style.opacity = "0";

    nextSlide.style.backgroundImage =
      `url("${backgroundImages[currentImageIndex]}")`;

    void nextSlide.offsetWidth;

    nextSlide.style.transition =
      "transform 1.4s ease-in-out, opacity 1.4s ease-in-out";

    currentSlide.style.transform = "translateX(-100%)";
    currentSlide.style.opacity = "0";

    nextSlide.classList.add("active");
    nextSlide.style.transform = "translateX(0)";
    nextSlide.style.opacity = "1";

    setTimeout(() => {
      currentSlide.classList.remove("active");
      currentSlide.style.transition = "none";
      currentSlide.style.transform = "translateX(100%)";
    }, 1400);

    activeSlideIndex = nextSlideIndex;
  }

  setInterval(changeBackground, 7000);
}

// =========================================================
// RISK HISTORY CHART
// =========================================================

async function loadRiskHistoryChart() {
  const canvas = document.getElementById(
    "risk-history-chart"
  );

  if (!canvas) {
    return;
  }

  const response = await apiFetch(
    "/risk/history?days=30&limit=30"
  );

  if (!response.ok) {
    return;
  }

  const data = await response.json();

  const assessments = (
    data.assessments || []
  ).slice().reverse();

  const labels = assessments.map((assessment) =>
    new Date(
      assessment.assessment_date
    ).toLocaleDateString()
  );

  const scores = assessments.map((assessment) =>
    Number(assessment.injury_percentage || 0)
  );

  if (riskHistoryChartInstance) {
    riskHistoryChartInstance.destroy();
  }

  riskHistoryChartInstance = new Chart(
    canvas.getContext("2d"),
    {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Injury Risk %",
            data: scores,
            tension: 0.25,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            suggestedMax: 100
          }
        }
      }
    }
  );

  loadTrainingIntensityChart(scores);
}


// =========================================================
// TRAINING INTENSITY CHART
// =========================================================

function loadTrainingIntensityChart(scores) {
  const canvas = document.getElementById(
    "training-intensity-chart"
  );

  if (!canvas || typeof Chart === "undefined") {
    return;
  }

  const recentScores = scores.slice(-5);

  if (trainingIntensityChartInstance) {
    trainingIntensityChartInstance.destroy();
  }

  trainingIntensityChartInstance = new Chart(
    canvas.getContext("2d"),
    {
      type: "bar",
      data: {
        labels: recentScores.map(
          (_, index) => `A${index + 1}`
        ),
        datasets: [
          {
            label: "Risk %",
            data: recentScores
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            display: false
          },
          y: {
            beginAtZero: true,
            suggestedMax: 100,
            display: false
          }
        }
      }
    }
  );
}


// =========================================================
// WEEKLY EXERCISE CHART
// =========================================================

async function loadExerciseSessionsChart() {
  const canvas = document.getElementById(
    "exercises-chart"
  );

  if (!canvas) {
    return;
  }

  const response = await apiFetch(
    "/exercises?days=7&limit=200"
  );

  if (!response.ok) {
    return;
  }

  const data = await response.json();
  const exercises = data.exercises || [];

  const dailySessions = buildSevenDayExerciseData(
    exercises
  );

  if (exercisesChartInstance) {
    exercisesChartInstance.destroy();
  }

  exercisesChartInstance = new Chart(
    canvas.getContext("2d"),
    {
      type: "bar",
      data: {
        labels: dailySessions.labels,
        datasets: [
          {
            label: "Sessions",
            data: dailySessions.values
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0
            }
          }
        }
      }
    }
  );
}


function buildSevenDayExerciseData(exercises) {
  const labels = [];
  const values = [];
  const dateMap = {};

  for (const exercise of exercises) {
    if (!exercise.date) {
      continue;
    }

    dateMap[exercise.date] =
      (dateMap[exercise.date] || 0) + 1;
  }

  for (let offset = 6; offset >= 0; offset -= 1) {
    const date = new Date();

    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() - offset);

    const key = formatLocalDate(date);

    labels.push(
      date.toLocaleDateString(undefined, {
        weekday: "short"
      })
    );

    values.push(dateMap[key] || 0);
  }

  return {
    labels,
    values
  };
}


function formatLocalDate(date) {
  const year = date.getFullYear();

  const month = String(
    date.getMonth() + 1
  ).padStart(2, "0");

  const day = String(
    date.getDate()
  ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

// =========================================================
// ATHLETE CHART LOADER
// =========================================================

window.loadAthleteCharts = async function () {
    if (
        typeof apiFetch !== "function" ||
        typeof Chart === "undefined"
    ) {
        return;
    }

    await Promise.allSettled([
        loadRiskHistoryChart(),
        loadExerciseSessionsChart(),
        loadTrainingIntensityChart()
    ]);
};


// =========================================================
// RISK HISTORY CHART
// One point per day
// =========================================================

async function loadRiskHistoryChart() {
    const canvas =
        document.getElementById("risk-history-chart");

    if (!canvas) {
        return;
    }

    try {
        const response = await apiFetch(
            "/risk/history?days=30&limit=100"
        );

        if (!response.ok) {
            return;
        }

        const data = await response.json();

        const assessments = data.assessments || [];

        // Group assessments by date.
        // If multiple assessments exist on the same day,
        // keep the most recent one.
        const dailyAssessments = {};

        assessments.forEach((assessment) => {
            if (!assessment.assessment_date) {
                return;
            }

            const date =
                new Date(assessment.assessment_date);

            const key =
                formatLocalDate(date);

            if (
                !dailyAssessments[key] ||
                new Date(assessment.assessment_date) >
                new Date(
                    dailyAssessments[key].assessment_date
                )
            ) {
                dailyAssessments[key] = assessment;
            }
        });

        const sortedDates =
            Object.keys(dailyAssessments).sort();

        const labels = sortedDates.map((dateString) => {
            const parts = dateString.split("-");

            const date = new Date(
                Number(parts[0]),
                Number(parts[1]) - 1,
                Number(parts[2])
            );

            return date.toLocaleDateString(
                undefined,
                {
                    month: "short",
                    day: "numeric"
                }
            );
        });

        const scores = sortedDates.map((dateString) => {
            return Number(
                dailyAssessments[dateString]
                    .injury_percentage || 0
            );
        });

        if (riskHistoryChartInstance) {
            riskHistoryChartInstance.destroy();
        }

        riskHistoryChartInstance =
            new Chart(
                canvas.getContext("2d"),
                {
                    type: "line",

                    data: {
                        labels: labels,

                        datasets: [
                            {
                                label: "Injury Risk %",
                                data: scores,
                                tension: 0.35,
                                fill: true,
                                pointRadius: 4,
                                pointHoverRadius: 6
                            }
                        ]
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,

                        interaction: {
                            mode: "index",
                            intersect: false
                        },

                        plugins: {
                            legend: {
                                display: true
                            }
                        },

                        scales: {
                            y: {
                                beginAtZero: true,
                                suggestedMax: 100,

                                ticks: {
                                    callback: function (value) {
                                        return value + "%";
                                    }
                                }
                            }
                        }
                    }
                }
            );

    } catch (error) {
        console.error(
            "Could not load risk chart:",
            error
        );
    }
}


// =========================================================
// WEEKLY EXERCISE CHART
// =========================================================

async function loadExerciseSessionsChart() {
    const canvas =
        document.getElementById("exercises-chart");

    if (!canvas) {
        return;
    }

    try {
        const response = await apiFetch(
            "/exercises?days=7&limit=200"
        );

        if (!response.ok) {
            return;
        }

        const data = await response.json();

        const exercises =
            data.exercises || [];

        const dailySessions =
            buildSevenDayExerciseData(exercises);

        if (exercisesChartInstance) {
            exercisesChartInstance.destroy();
        }

        exercisesChartInstance =
            new Chart(
                canvas.getContext("2d"),
                {
                    type: "bar",

                    data: {
                        labels:
                            dailySessions.labels,

                        datasets: [
                            {
                                label: "Sessions",
                                data:
                                    dailySessions.values,
                                borderRadius: 6
                            }
                        ]
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,

                        plugins: {
                            legend: {
                                display: true
                            }
                        },

                        scales: {
                            y: {
                                beginAtZero: true,

                                ticks: {
                                    precision: 0,
                                    stepSize: 1
                                }
                            }
                        }
                    }
                }
            );

    } catch (error) {
        console.error(
            "Could not load exercise chart:",
            error
        );
    }
}


// =========================================================
// BUILD LAST 7 DAYS
// =========================================================

function buildSevenDayExerciseData(exercises) {
    const labels = [];
    const values = [];

    const dateMap = {};

    exercises.forEach((exercise) => {
        if (!exercise.date) {
            return;
        }

        dateMap[exercise.date] =
            (dateMap[exercise.date] || 0) + 1;
    });

    // Today + previous 6 days
    for (
        let offset = 6;
        offset >= 0;
        offset--
    ) {
        const date = new Date();

        date.setHours(0, 0, 0, 0);

        date.setDate(
            date.getDate() - offset
        );

        const key =
            formatLocalDate(date);

        labels.push(
            date.toLocaleDateString(
                undefined,
                {
                    weekday: "short"
                }
            )
        );

        values.push(
            dateMap[key] || 0
        );
    }

    return {
        labels: labels,
        values: values
    };
}


// =========================================================
// TRAINING INTENSITY CHART
// =========================================================

async function loadTrainingIntensityChart() {
    const canvas =
        document.getElementById(
            "training-intensity-chart"
        );

    if (!canvas) {
        return;
    }

    try {
        const response = await apiFetch(
            "/exercises?days=30&limit=200"
        );

        if (!response.ok) {
            return;
        }

        const data =
            await response.json();

        const exercises =
            data.exercises || [];

        const intensityCounts = {
            low: 0,
            moderate: 0,
            high: 0,
            very_high: 0
        };

        exercises.forEach((exercise) => {
            const intensity =
                String(
                    exercise.intensity || ""
                ).toLowerCase();

            if (
                Object.prototype.hasOwnProperty.call(
                    intensityCounts,
                    intensity
                )
            ) {
                intensityCounts[intensity]++;
            }
        });

        const labels = [
            "Low",
            "Moderate",
            "High",
            "Very High"
        ];

        const values = [
            intensityCounts.low,
            intensityCounts.moderate,
            intensityCounts.high,
            intensityCounts.very_high
        ];

        if (trainingIntensityChartInstance) {
            trainingIntensityChartInstance.destroy();
        }

        trainingIntensityChartInstance =
            new Chart(
                canvas.getContext("2d"),
                {
                    type: "bar",

                    data: {
                        labels: labels,

                        datasets: [
                            {
                                label: "Sessions",
                                data: values,
                                borderRadius: 6
                            }
                        ]
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,

                        plugins: {
                            legend: {
                                display: false
                            }
                        },

                        scales: {
                            y: {
                                beginAtZero: true,

                                ticks: {
                                    precision: 0,
                                    stepSize: 1
                                }
                            }
                        }
                    }
                }
            );

    } catch (error) {
        console.error(
            "Could not load intensity chart:",
            error
        );
    }
}


// =========================================================
// DATE FORMAT HELPER
// =========================================================

function formatLocalDate(date) {
    const year =
        date.getFullYear();

    const month =
        String(
            date.getMonth() + 1
        ).padStart(2, "0");

    const day =
        String(
            date.getDate()
        ).padStart(2, "0");

    return `${year}-${month}-${day}`;
}