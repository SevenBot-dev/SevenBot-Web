console.debug("%cLoaded: status.js", "color:#5865f2")

function main(rawChartData) {
  function roundAt(base, index) {
    return Math.round(base * (10 ** index)) / (10 ** index)
  }
  Highcharts.setOptions({
    time: {
      timezone: 'asia/tokyo'
    },
    lang: {
      decimalPoint: '.',
      thousandsSep: ''
    }
  });
  chartDataPing = []
  chartDataDBPing = []
  chartDataWebPing = []
  chartDataGuilds = []
  chartDataUsers = []
  chartDataCPU = []
  chartDataMemory = []
  chartDataSave = []
  chartDataDB = []
  rawChartData.forEach((d, i) => {
    date = Math.floor(d["time"] * 1000)
    chartDataPing.push(
      [date, d["ping"]]
    )
    if (d["db_ping"]) {
      chartDataDBPing.push(
        [date, d["db_ping"]]
      )
      chartDataWebPing.push(
        [date, d["web_ping"]]
      )
    }
    chartDataGuilds.push(
      [date, d["guilds"]]
    )
    chartDataUsers.push(
      [date, d["users"]]
    )
    chartDataCPU.push(
      [date, d["cpu"]]
    )
    chartDataMemory.push({
      x: date,
      y: d["mem"]["percent"],
      percent: d["mem"]["percent"],
      real: d["mem"]["gb"]
    })
    if (d["save"]) {
      chartDataSave.push(
        [date, roundAt(d["save"]["main"], 1)]
      )
      chartDataDB.push(
        [date, roundAt(d["save"]["db"], 1)]
      )
    }

  })
  pingAvg = roundAt(chartDataPing.reduce((a, b) => a + b[1], 0) / chartDataPing.length, 2)
  webPingAvg = roundAt(chartDataWebPing.reduce((a, b) => a + b[1], 0) / chartDataWebPing.length, 2)
  dbPingAvg = roundAt(chartDataDBPing.reduce((a, b) => a + b[1], 0) / chartDataDBPing.length, 2)
  console.log(webPingAvg, dbPingAvg)
  chartPing = Highcharts.chart('chart-ping', {
    chart: {
      // styledMode: true
      backgroundColor: "var(--background-secondary)",

      // panning: true,

    },
    colors: ["#1abc9c", "#607d8b", "#979c9f"],
    title: {
      style: {
        color: "var(--text-normal)"
      },
      text: 'Ping（Botの通信速度）',
    },
    yAxis: [{
      gridLineColor: "var(--status-x-axis-color)",
      title: {
        text: 'Discord',
        style: {
          color: "var(--interactive-normal)"
        }
      },
      labels: {
        // format: '{value}ms',
        style: {
          color: "var(--interactive-normal)"
        }
      },
      plotLines: [{
          value: pingAvg,
          color: '#11806a',
          width: 2,
        },
        {
          value: dbPingAvg,
          color: '#546e7a',
          width: 2,
        }
      ],
      allowDecimals: false,
      showInLegend: false,
      title: {
        text: "ms",
        offset: 0,
        align: "high",
        rotation: 0,
        y: -10,
        style: {
          color: "var(--interactive-normal)"
        },
      },

    }],

    xAxis: {
      type: 'datetime',
      dateTimeLabelFormats: {
        millisecond: '%H:%M',
        day: "%m/%d %H:%M"
      },
      tickLength: 0,
      crosshair: {
        color: "var(--background-tertiary)"
      },
      lineColor: "var(--status-x-axis-color)",
      labels: {
        style: {
          color: "var(--interactive-normal)"
        }
      },
    },
    legend: {
      layout: 'vertical',
      align: 'right',
      verticalAlign: 'middle'
    },

    plotOptions: {
      series: {
        label: {
          connectorAllowed: false
        },
        marker: {
          enabled: false
        },
        pointStart: 2010
      }
    },

    series: [{
        name: 'Discord',
        data: chartDataPing,
        yAxis: 0,
        zIndex: 1,
        tooltip: {
          valuePrefix: '',
          valueSuffix: 'ms',
        },
        showInLegend: false,
        marker: {
          symbol: "circle"
        }
      },
      {
        name: 'MongoDB',
        data: chartDataDBPing,
        yAxis: 0,
        tooltip: {
          valuePrefix: '',
          valueSuffix: 'ms',
        },
        showInLegend: false,
        marker: {
          symbol: "circle"
        }
      }
    ],

    tooltip: {
      xDateFormat: "%m/%d %H:%M",
      backgroundColor: "var(--status-tooltip-color)",
      borderWidth: 0,
      shadow: false,
      zIndex: 20,
      style: {
        color: "var(--text-normal)"
      }
    },
    credits: {
      enabled: false
    },

  });
  chartUser = Highcharts.chart('chart-guild-user', {
    chart: {
      // styledMode: true
      backgroundColor: "var(--background-secondary)",


    },
    colors: ["#2ecc71", "#3498db"],
    title: {
      style: {
        color: "var(--text-normal)"
      },
      text: 'サーバー数、認識できるユーザー数',
    },
    yAxis: [{
      gridLineColor: "var(--status-x-axis-color)",
      title: {
        text: 'サーバー数',
        style: {
          color: "#2ecc71"
        }
      },
      labels: {
        style: {
          color: "#2ecc71"
        }
      },
      allowDecimals: false,

      title: {
        text: "サーバー",
        align: "high",
        offset: 0,
        rotation: 0,
        y: -10,
        style: {
          color: "#2ecc71"
        }
      }
    }, {
      gridLineWidth: 0,
      title: {
        text: 'ユーザー数',
        style: {
          color: "#3498db"
        }
      },
      labels: {
        // format: '{value}ユーザー',
        style: {
          color: "#3498db"
        }
      },
      allowDecimals: false,
      opposite: true,

      title: {
        text: "ユーザー",
        offset: 0,
        align: "high",
        rotation: 0,
        y: -10,
        style: {
          color: "#3498db"
        }
      }
    }],

    xAxis: {
      type: 'datetime',
      dateTimeLabelFormats: {
        millisecond: '%H:%M',
        day: "%m/%d %H:%M"
      },
      tickLength: 0,
      crosshair: {
        color: "var(--background-tertiary)"
      },
      lineColor: "var(--status-x-axis-color)",
      labels: {
        style: {
          color: "var(--interactive-normal)"
        }
      }
    },
    credits: {
      enabled: false
    },
    legend: {
      layout: 'vertical',
      align: 'right',
      verticalAlign: 'middle'
    },

    plotOptions: {
      series: {
        label: {
          connectorAllowed: false
        },
        marker: {
          enabled: false
        },
        pointStart: 2010
      }
    },

    series: [{
      name: 'サーバー数',
      data: chartDataGuilds,
      yAxis: 0,
      showInLegend: false,
      marker: {
        symbol: "circle"
      },
      tooltip: {
        valuePrefix: "",
        valueSuffix: 'サーバー',
      },
    }, {
      name: 'ユーザー数',
      data: chartDataUsers,
      yAxis: 1,
      tooltip: {
        valuePrefix: '',
        valueSuffix: 'ユーザー',
      },
      showInLegend: false,
      marker: {
        symbol: "circle"
      }
    }],
    tooltip: {
      xDateFormat: "%m/%d %H:%M",
      backgroundColor: "var(--status-tooltip-color)",
      borderWidth: 0,
      shadow: false,
      style: {
        color: "var(--text-normal)"
      }
    },

  });
  chartVPS = Highcharts.chart('chart-guild-vps', {
    chart: {
      // styledMode: true
      backgroundColor: "var(--background-secondary)",


    },
    colors: ["#9b59b6", "#e91e63"],
    title: {
      style: {
        color: "var(--text-normal)"
      },
      text: 'CPU、メモリの使用率',
    },
    yAxis: [{
      gridLineColor: "var(--status-x-axis-color)",
      labels: {
        style: {
          color: "var(--interactive-normal)"
        }
      },
      min: 0,
      max: 100,
      allowDecimals: false,

      title: {
        text: "%",
        align: "high",
        offset: 0,
        rotation: 0,
        y: -10,
        style: {
          color: "var(--interactive-normal)"
        }
      }
    }],

    xAxis: {
      type: 'datetime',
      dateTimeLabelFormats: {
        millisecond: '%H:%M',
        day: "%m/%d %H:%M"
      },
      tickLength: 0,
      crosshair: {
        color: "var(--background-tertiary)"
      },
      lineColor: "var(--status-x-axis-color)",
      labels: {
        style: {
          color: "var(--interactive-normal)"
        }
      }
    },
    credits: {
      enabled: false
    },
    legend: {
      layout: 'vertical',
      align: 'right',
      verticalAlign: 'middle'
    },

    plotOptions: {
      series: {
        label: {
          connectorAllowed: false
        },
        marker: {
          enabled: false
        },
        pointStart: 2010
      }
    },

    series: [{
      name: 'CPU',
      data: chartDataCPU,
      yAxis: 0,
      showInLegend: false,
      marker: {
        symbol: "circle"
      },
      tooltip: {
        valuePrefix: "",
        valueSuffix: '%',
      },
    }, {
      name: 'メモリ',
      data: chartDataMemory,
      yAxis: 0,
      tooltip: {
        pointFormatter: function() {
          return `<tspan style="fill:#e91e63">●</tspan> メモリ使用率: <tspan style="font-weight:bold;">${this.percent}%</tspan><tspan class="highcharts-br">​</tspan>` +
            `<tspan style="fill:#0000">●</tspan> メモリ使用量: <tspan style="font-weight:bold;">${Math.floor(this.real * 100) / 100}GB</tspan><tspan class="highcharts-br">​</tspan>`
        }
      },
      showInLegend: false,
      marker: {
        symbol: "circle"
      },
      turboThreshold: 5000
    }],
    tooltip: {
      xDateFormat: "%m/%d %H:%M",
      backgroundColor: "var(--status-tooltip-color)",
      borderWidth: 0,
      shadow: false,
      style: {
        color: "var(--text-normal)"
      }
    },

  });
  chartSave = Highcharts.chart('chart-guild-save', {
    chart: {
      // styledMode: true
      backgroundColor: "var(--background-secondary)",


    },
    colors: ["#f1c40f", "#e67e22"],
    title: {
      style: {
        color: "var(--text-normal)"
      },
      text: 'セーブデータの容量',
    },
    yAxis: [{
      gridLineColor: "var(--status-x-axis-color)",
      labels: {
        style: {
          color: "var(--interactive-normal)"
        }
      },

      title: {
        text: "KB",
        align: "high",
        offset: 0,
        rotation: 0,
        y: -10,
        style: {
          color: "var(--interactive-normal)"
        }
      }
    }],

    xAxis: {
      type: 'datetime',
      dateTimeLabelFormats: {
        millisecond: '%H:%M',
        day: "%m/%d %H:%M"
      },
      tickLength: 0,
      crosshair: {
        color: "var(--background-tertiary)"
      },
      lineColor: "var(--status-x-axis-color)",
      labels: {
        style: {
          color: "var(--interactive-normal)"
        }
      }
    },
    credits: {
      enabled: false
    },
    legend: {
      layout: 'vertical',
      align: 'right',
      verticalAlign: 'middle'
    },

    plotOptions: {
      series: {
        label: {
          connectorAllowed: false
        },
        marker: {
          enabled: false
        },
        pointStart: 2010
      }
    },

    series: [{
      name: 'データベース',
      data: chartDataDB,
      yAxis: 0,
      tooltip: {
        valuePrefix: "",
        valueSuffix: 'KB',

      },
      showInLegend: false,
      marker: {
        symbol: "circle"
      }
    }],
    tooltip: {
      xDateFormat: "%m/%d %H:%M",
      backgroundColor: "var(--status-tooltip-color)",
      borderWidth: 0,
      shadow: false,
      style: {
        color: "var(--text-normal)"
      }
    },

  });
  chartPing.reflow()
  chartUser.reflow()
  chartVPS.reflow()
  chartSave.reflow()
  document.querySelector('.loading').style.display = 'none'
  document.querySelector('#charts-container').classList.remove('hidden')
}

(fetch("/status/api").then(
  resp => resp.json()
)).then(data => {
  mainInterval = setInterval(async () => {
    if (typeof Highcharts != "undefined") {
      clearInterval(mainInterval)
      main(data)
    }
  }, 10)
})