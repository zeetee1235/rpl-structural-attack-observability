#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)

find_latest <- function(pattern, dir = ".") {
  files <- list.files(dir, pattern = pattern, full.names = TRUE)
  if (length(files) == 0) return(NA)
  files[which.max(file.info(files)$mtime)]
}

summary_csv <- if (length(args) >= 1) args[1] else find_latest("^simulation_summary_.*\\.csv$", "simulations/output")
if (is.na(summary_csv)) {
  stop("No simulation_summary_*.csv found in simulations/output")
}

output_dir <- if (length(args) >= 2) args[2] else "docs/figures"
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

coords_md <- "simulations/scenarios/SCENARIO_COORDINATES.md"

ieee_png <- function(filename, width = 1800, height = 1200) {
  png(filename, width = width, height = height, res = 300, type = "cairo")
}

ieee_pdf <- function(filename, width = 6, height = 4) {
  pdf(filename, width = width, height = height, family = "serif")
}

ieee_par <- function() {
  par(
    bg = "white",
    cex.axis = 0.9,
    cex.lab = 1.0,
    cex.main = 1.0,
    mar = c(4, 4, 2, 1)
  )
}

t_critical_95 <- function(n) {
  if (n <= 1) return(0.0)
  table <- c(
    "2" = 12.706, "3" = 4.303, "4" = 3.182, "5" = 2.776,
    "6" = 2.571, "7" = 2.447, "8" = 2.365, "9" = 2.306, "10" = 2.262
  )
  if (!is.na(table[as.character(n)])) return(table[as.character(n)])
  return(1.96)
}

df <- read.csv(summary_csv, stringsAsFactors = FALSE)
df$attack_rate_logged <- as.numeric(df$attack_rate_logged)
df$pdr_clipped <- as.numeric(df$pdr_clipped)
df$exposure_e1_prime <- as.numeric(df$exposure_e1_prime)
df$num_nodes <- as.integer(df$num_nodes)

agg_stats <- function(data) {
  out <- aggregate(
    pdr_clipped ~ scenario + attack_rate_logged,
    data = data,
    function(x) c(mean = mean(x), sd = sd(x), n = length(x))
  )
  out$mean <- out$pdr_clipped[, "mean"]
  out$sd <- out$pdr_clipped[, "sd"]
  out$n <- out$pdr_clipped[, "n"]
  out$ci <- mapply(function(sd, n) {
    t_critical_95(n) * (sd / sqrt(n))
  }, out$sd, out$n)
  out$pdr_clipped <- NULL
  out
}

agg <- agg_stats(df)

save_plot <- function(name, width = 6, height = 4, expr) {
  ieee_pdf(file.path(output_dir, paste0(name, ".pdf")), width = width, height = height)
  ieee_par()
  expr()
  dev.off()
  ieee_png(file.path(output_dir, paste0(name, ".png")), width = width * 300, height = height * 300)
  ieee_par()
  expr()
  dev.off()
}

plot_workflow <- function() {
  plot.new()
  par(mar = c(2, 2, 1, 1))
  plot.window(xlim = c(0, 12), ylim = c(0, 10))
  boxes <- list(
    list(x = 1, y = 8.2, label = "Scenario (.csc)"),
    list(x = 1, y = 6.4, label = "Firmware Build"),
    list(x = 1, y = 4.6, label = "Cooja Headless"),
    list(x = 1, y = 2.8, label = "COOJA.testlog"),
    list(x = 7, y = 2.8, label = "Analyzer"),
    list(x = 7, y = 4.6, label = "CSV / Results")
  )
  for (b in boxes) {
    rect(b$x, b$y, b$x + 4, b$y + 1, border = "black", col = "white")
    text(b$x + 2, b$y + 0.5, b$label, cex = 1.0)
  }
  arrows(3, 8.2, 3, 7.4, length = 0.1)
  arrows(3, 6.4, 3, 5.6, length = 0.1)
  arrows(3, 4.6, 3, 3.8, length = 0.1)
  arrows(5.2, 3.3, 7, 3.3, length = 0.1)
  arrows(9, 3.8, 9, 4.6, length = 0.1)
  text(9, 5.9, "Report", cex = 1.0)
}

plot_arch <- function() {
  plot.new()
  par(mar = c(2, 2, 1, 1))
  plot.window(xlim = c(0, 10), ylim = c(0, 10))
  labels <- c(
    "Queue Manager",
    "DIO Queue Option",
    "Neighbor Table",
    "QuickTheta / Beta",
    "Weight Computation",
    "Parent Selection"
  )
  y <- seq(9, 2, length.out = length(labels))
  for (i in seq_along(labels)) {
    rect(1.5, y[i] - 0.6, 8.5, y[i] + 0.6, border = "black", col = "white")
    text(5, y[i], labels[i], cex = 1.0)
    if (i < length(labels)) {
      arrows(5, y[i] - 0.6, 5, y[i + 1] + 0.6, length = 0.1)
    }
  }
}

parse_scenario_coords <- function(md_file) {
  lines <- readLines(md_file, warn = FALSE)
  scenarios <- list()
  current <- NULL
  for (line in lines) {
    if (grepl("^Scenario [A-D]:", line)) {
      current <- sub("^Scenario ([A-D]).*$", "\\1", line)
      scenarios[[current]] <- data.frame()
    } else if (!is.null(current) && grepl("^\\|", line)) {
      if (grepl("\\| ---", line)) next
      cols <- strsplit(line, "\\|")[[1]]
      cols <- trimws(cols)
      cols <- cols[cols != ""]
      if (length(cols) >= 4 && cols[1] != "node_id") {
        scenarios[[current]] <- rbind(
          scenarios[[current]],
          data.frame(
            node_id = as.integer(cols[1]),
            role = cols[2],
            x = as.numeric(cols[3]),
            y = as.numeric(cols[4]),
            stringsAsFactors = FALSE
          )
        )
      }
    }
  }
  scenarios
}

plot_topologies <- function() {
  sc <- parse_scenario_coords(coords_md)
  par(mfrow = c(2, 2), mar = c(3, 3, 2, 1))
  for (name in c("A", "B", "C", "D")) {
    dat <- sc[[name]]
    plot(dat$x, dat$y, type = "n", xlab = "x (m)", ylab = "y (m)", main = paste("Scenario", name))
    for (i in seq_len(nrow(dat))) {
      role <- dat$role[i]
      pch <- if (role == "root") 15 else if (role == "attacker") 17 else if (role == "relay") 0 else 1
      col <- if (role == "attacker") "gray20" else "black"
      points(dat$x[i], dat$y[i], pch = pch, col = col)
      text(dat$x[i], dat$y[i] + 2, dat$node_id[i], cex = 0.7)
    }
  }
  par(mfrow = c(1, 1))
}

plot_parent_selection <- function() {
  plot(0, 0, type = "n", xlim = c(0, 1), ylim = c(0, 1),
       xlab = "Normalized RPL cost (p-hat)", ylab = "Normalized Backpressure (deltaQ-hat)",
       main = "Parent Selection Model", xaxt = "n", yaxt = "n")
  axis(1, at = seq(0, 1, by = 0.2))
  axis(2, at = seq(0, 1, by = 0.2), las = 1)
  grid(col = "gray85", lty = "dotted")
  thetas <- c(0.2, 0.5, 0.8)
  w <- 0.5
  for (t in thetas) {
    x <- seq(0, 1, length.out = 100)
    y <- (t / (1 - t)) * x - (w / (1 - t))
    y[y < 0] <- NA
    y[y > 1] <- NA
    lines(x, y, lty = ifelse(t == 0.5, 1, 2), col = "black")
    text(0.82, (t / (1 - t)) * 0.82 - (w / (1 - t)), paste("theta=", t), cex = 0.75, pos = 4)
  }
  text(0.12, 0.9, "Higher theta -> RPL-weighted", cex = 0.8)
  text(0.12, 0.1, "Lower theta -> Backpressure-weighted", cex = 0.8)
}

plot_pdr_vs_alpha <- function(scenarios, title, filename) {
  sub <- agg[agg$scenario %in% scenarios, ]
  alphas <- sort(unique(sub$attack_rate_logged))
  plot(0, 0, type = "n", xlim = range(alphas), ylim = c(0, 1.05),
       xlab = "Attack rate (alpha)", ylab = "PDR*", main = title)
  cols <- c("black", "gray40", "gray70", "gray20")
  pchs <- c(16, 17, 15, 1)
  label_map <- c(
    "scenario_a_low_exposure" = "A",
    "scenario_b_high_exposure" = "B",
    "scenario_b_high_exposure_20" = "B20",
    "scenario_c_high_pd" = "C",
    "scenario_d_apl_bc" = "D"
  )
  for (i in seq_along(scenarios)) {
    sc <- scenarios[i]
    d <- sub[sub$scenario == sc, ]
    d <- d[order(d$attack_rate_logged), ]
    lines(d$attack_rate_logged, d$mean, type = "b", lty = i, pch = pchs[i], col = cols[i])
    arrows(d$attack_rate_logged, d$mean - d$ci, d$attack_rate_logged, d$mean + d$ci,
           angle = 90, code = 3, length = 0.03, col = cols[i])
  }
  legend_labels <- sapply(scenarios, function(s) ifelse(!is.na(label_map[s]), label_map[s], s))
  legend("topright", legend = legend_labels, lty = seq_along(scenarios), pch = pchs, col = cols, cex = 0.8)
}

plot_exposure_vs_pdr <- function() {
  mix_path <- "data/exposure_mix.csv"
  use_mix <- file.exists(mix_path)
  if (use_mix) {
    mix <- read.csv(mix_path, stringsAsFactors = FALSE)
    exp_df <- aggregate(
      cbind(E_mix, attack_rate) ~ scenario,
      data = mix,
      function(x) mean(as.numeric(x), na.rm = TRUE)
    )
    pdr_df <- aggregate(
      pdr_clipped ~ scenario + attack_rate_logged,
      data = df,
      mean
    )
    # merge on scenario and attack_rate
    merged <- merge(
      pdr_df,
      mix,
      by.x = c("scenario", "attack_rate_logged"),
      by.y = c("scenario", "attack_rate"),
      all.x = TRUE
    )
    plot(merged$E_mix, merged$pdr_clipped,
         xlab = "Exposure (E_mix)", ylab = "PDR*", pch = 16, col = "black",
         main = "Exposure vs PDR*")
    valid <- merged[is.finite(merged$E_mix) & is.finite(merged$pdr_clipped), ]
    if (nrow(valid) >= 2) {
      fit <- lm(pdr_clipped ~ E_mix, data = valid)
      cf <- coef(fit)
      if (all(is.finite(cf))) {
        abline(fit, col = "gray40", lwd = 2)
      }
    }
  } else {
    exp_df <- aggregate(
      cbind(pdr_clipped, exposure_e1_prime) ~ scenario + attack_rate_logged,
      data = df,
      function(x) mean(x, na.rm = TRUE)
    )
    plot(exp_df$exposure_e1_prime, exp_df$pdr_clipped,
         xlab = "Exposure (E1')", ylab = "PDR*", pch = 16, col = "black",
         main = "Exposure vs PDR*")
    valid <- exp_df[is.finite(exp_df$exposure_e1_prime) & is.finite(exp_df$pdr_clipped), ]
    if (nrow(valid) >= 2) {
      fit <- lm(pdr_clipped ~ exposure_e1_prime, data = valid)
      cf <- coef(fit)
      if (all(is.finite(cf))) {
        abline(fit, col = "gray40", lwd = 2)
      }
    }
  }
}

plot_heatmap <- function() {
  exp_df <- aggregate(
    pdr_clipped ~ scenario + attack_rate_logged,
    data = df,
    mean
  )
  scenarios <- sort(unique(exp_df$scenario))
  label_map <- c(
    "scenario_a_low_exposure" = "A",
    "scenario_b_high_exposure" = "B",
    "scenario_b_high_exposure_20" = "B20",
    "scenario_c_high_pd" = "C",
    "scenario_d_apl_bc" = "D"
  )
  short_labels <- sapply(scenarios, function(s) ifelse(!is.na(label_map[s]), label_map[s], s))
  alphas <- sort(unique(exp_df$attack_rate_logged))
  mat <- matrix(NA, nrow = length(scenarios), ncol = length(alphas))
  for (i in seq_along(scenarios)) {
    for (j in seq_along(alphas)) {
      v <- exp_df$pdr_clipped[exp_df$scenario == scenarios[i] & exp_df$attack_rate_logged == alphas[j]]
      if (length(v) > 0) mat[i, j] <- v[1]
    }
  }
  image(
    x = alphas, y = seq_along(scenarios), z = t(mat),
    xlab = "Attack rate (alpha)", ylab = "Scenario",
    col = gray(seq(0.9, 0.2, length.out = 10)),
    axes = FALSE, main = "Observability Heatmap (PDR*)"
  )
  axis(1, at = alphas, labels = alphas)
  axis(2, at = seq_along(scenarios), labels = short_labels, las = 2)
}

parse_parent_composition <- function() {
  testlogs <- list.files("simulations/output", pattern = "_COOJA\\.testlog$", full.names = TRUE)
  if (length(testlogs) == 0) return(NULL)
  results <- data.frame()
  for (f in testlogs) {
    scenario <- sub("^(.+)_\\d{8}_\\d{6}_COOJA\\.testlog$", "\\1", basename(f))
    lines <- readLines(f, warn = FALSE)
    attacker_id <- NA
    for (line in lines) {
      if (grepl("ATTACK_START", line)) {
        m <- regmatches(line, regexec("node=(\\d+)", line))[[1]]
        if (length(m) >= 2) attacker_id <- as.integer(m[2])
      }
    }
    if (is.na(attacker_id)) next
    parent_lines <- lines[grepl("ev=PARENT", lines)]
    if (length(parent_lines) == 0) next
    parent_ids <- sapply(parent_lines, function(x) {
      m <- regmatches(x, regexec("parent=(\\d+)", x))[[1]]
      if (length(m) >= 2) return(as.integer(m[2]))
      return(NA)
    })
    parent_ids <- parent_ids[!is.na(parent_ids)]
    if (length(parent_ids) == 0) next
    direct <- sum(parent_ids == 1)
    via_attacker <- sum(parent_ids == attacker_id)
    via_relay <- sum(parent_ids != 1 & parent_ids != attacker_id)
    results <- rbind(results, data.frame(
      scenario = scenario,
      direct = direct,
      via_attacker = via_attacker,
      via_relay = via_relay
    ))
  }
  if (nrow(results) == 0) return(NULL)
  agg <- aggregate(cbind(direct, via_attacker, via_relay) ~ scenario, data = results, sum)
  totals <- agg$direct + agg$via_attacker + agg$via_relay
  agg$direct <- agg$direct / totals
  agg$via_attacker <- agg$via_attacker / totals
  agg$via_relay <- agg$via_relay / totals
  agg
}

plot_parent_composition <- function() {
  comp <- parse_parent_composition()
  if (is.null(comp)) {
    plot.new()
    text(0.5, 0.5, "No parent composition data", cex = 1.0)
    return()
  }
  scenarios <- comp$scenario
  short_labels <- gsub("scenario_", "", scenarios)
  short_labels <- gsub("_low_exposure", "A", short_labels)
  short_labels <- gsub("_high_exposure_20", "B20", short_labels)
  short_labels <- gsub("_high_exposure", "B", short_labels)
  short_labels <- gsub("_high_pd", "C", short_labels)
  short_labels <- gsub("_apl_bc", "D", short_labels)
  mat <- t(as.matrix(comp[, c("direct", "via_attacker", "via_relay")]))
  colnames(mat) <- short_labels
  op <- par(no.readonly = TRUE)
  par(mar = c(6, 4, 2, 1))
  barplot(
    mat,
    beside = FALSE,
    col = c("white", "gray50", "gray80"),
    border = "black",
    xlab = "Scenario",
    ylab = "Fraction",
    main = "Parent Composition",
    las = 2,
    cex.names = 0.8
  )
  legend("topright", legend = c("Direct-to-root", "Via attacker", "Via relay"),
         fill = c("white", "gray50", "gray80"), cex = 0.8)
  par(op)
}

write_tables <- function() {
  dir.create("docs/tables", showWarnings = FALSE, recursive = TRUE)
  table1 <- data.frame(
    parameter = c("node count", "attack rate alpha", "queue size", "MAC/RDC", "duration"),
    value = c("10, 20", "scenario-specific", "200 packets", "CSMA / NULLRDC", "3600s")
  )
  write.csv(table1, "docs/tables/table1_sim_params.csv", row.names = FALSE)

  table2 <- agg
  table2$mean <- round(table2$mean, 4)
  table2$ci <- round(table2$ci, 4)
  write.csv(table2, "docs/tables/table2_pdr_ci.csv", row.names = FALSE)
}

plot_exposure_comparison <- function() {
  comp_path <- "data/exposure_comparison.csv"
  if (!file.exists(comp_path)) {
    plot.new()
    text(0.5, 0.5, "No exposure_comparison.csv", cex = 1.0)
    return()
  }
  comp <- read.csv(comp_path, stringsAsFactors = FALSE)
  plot(comp$E_mix, comp$E_log,
       xlab = "E_mix", ylab = "E_log (proxy)",
       pch = 16, col = "black",
       main = "E_mix vs E_log")
  valid <- comp[is.finite(comp$E_mix) & is.finite(comp$E_log), ]
  if (nrow(valid) >= 2) {
    fit <- lm(E_log ~ E_mix, data = valid)
    cf <- coef(fit)
    if (all(is.finite(cf))) {
      abline(fit, col = "gray40", lwd = 2)
    }
  }
}

plot_pdr_vs_alpha_emix <- function() {
  comp_path <- "data/exposure_comparison.csv"
  if (!file.exists(comp_path)) {
    plot.new()
    text(0.5, 0.5, "No exposure_comparison.csv", cex = 1.0)
    return()
  }
  comp <- read.csv(comp_path, stringsAsFactors = FALSE)
  alpha <- as.numeric(comp$attack_rate)
  comp$xval <- alpha * comp$E_mix
  plot(comp$xval, comp$PDR_star,
       xlab = "alpha * E_mix", ylab = "PDR*",
       pch = 16, col = "black",
       main = "PDR* vs alpha * E_mix")
  valid <- comp[is.finite(comp$xval) & is.finite(comp$PDR_star), ]
  if (nrow(valid) >= 2) {
    fit <- lm(PDR_star ~ xval, data = valid)
    cf <- coef(fit)
    if (all(is.finite(cf))) {
      abline(fit, col = "gray40", lwd = 2)
    }
  }
}

save_plot("fig1_workflow", width = 6, height = 3, plot_workflow)
save_plot("fig2_topologies", width = 6, height = 5, plot_topologies)
save_plot("fig3_brpl_architecture", width = 6, height = 4, plot_arch)
save_plot("fig4_parent_selection_model", width = 6, height = 4, plot_parent_selection)
save_plot("fig5_pdr_vs_alpha_b", width = 6, height = 4, function() {
  plot_pdr_vs_alpha(c("scenario_b_high_exposure", "scenario_b_high_exposure_20"), "PDR* vs alpha (Scenario B)", "fig5")
})
save_plot("fig6_pdr_vs_alpha_abcd", width = 6, height = 4, function() {
  plot_pdr_vs_alpha(c("scenario_a_low_exposure", "scenario_b_high_exposure", "scenario_c_high_pd", "scenario_d_apl_bc"),
                    "PDR* vs alpha (A/B/C/D)", "fig6")
})
save_plot("fig7_exposure_vs_pdr", width = 6, height = 4, plot_exposure_vs_pdr)
save_plot("fig8_scale_effect", width = 6, height = 4, function() {
  plot_pdr_vs_alpha(c("scenario_b_high_exposure", "scenario_b_high_exposure_20"), "Scale Effect (10 vs 20)", "fig8")
})
save_plot("fig9_parent_composition", width = 6, height = 4, plot_parent_composition)
save_plot("fig10_observability_heatmap", width = 6, height = 4, plot_heatmap)
save_plot("fig11_emix_vs_elog", width = 6, height = 4, plot_exposure_comparison)
save_plot("fig12_pdr_vs_alpha_emix", width = 6, height = 4, plot_pdr_vs_alpha_emix)

write_tables()

cat("Figures saved to:", output_dir, "\n")
cat("Tables saved to: docs/tables/table1_sim_params.csv, docs/tables/table2_pdr_ci.csv\n")
