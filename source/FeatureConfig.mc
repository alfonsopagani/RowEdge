using Toybox.Application;

// Feature flags and the FIT log mode, set from the Settings menu.
class FeatureConfig {

    enum {
        FEAT_AUTO_PAUSE,
        FEAT_DEMO_MODE,
        FEAT_ACCEL_LOG,       // log mode: read from logMode, not a toggle
        FEAT_HFREQ_ACCEL,     // log mode
        FEAT_CURVE_METRICS,
        FEAT_ROWING_LOG,      // log mode
        FEAT_RADAR_LOG,       // log mode
        FEAT_SPARKLINES,
        FEAT_DARK_MODE,
        FEAT_AUTO_THRESHOLD,
        FEAT_RADAR_ALERTS,
        FEAT_ALERT_SOUND,
        FEAT_COUNT
    }

    // What the activity file records besides stroke rate and distance per
    // stroke. One mode at a time: they share the FIT record space.
    enum {
        LOG_OFF,
        LOG_ROWING,
        LOG_HF,
        LOG_ACCEL,
        LOG_RADAR,
        LOG_COUNT
    }

    // Storage keys of the toggles, by feature id (null: not a toggle)
    static const KEYS = ["feat_autoPause", "feat_demoMode", null, null,
                         "feat_curveMetrics", null, null, "feat_sparklines",
                         "feat_darkMode", "feat_autoThreshold",
                         "feat_radarAlerts", "feat_alertSound"];

    var enabled;
    var logMode = LOG_ROWING;

    function initialize() {
        enabled = new [FEAT_COUNT];
        load();
    }

    function load() {
        enabled[FEAT_AUTO_PAUSE] = loadBool("feat_autoPause", true);
        enabled[FEAT_DEMO_MODE] = loadBool("feat_demoMode", false);
        enabled[FEAT_CURVE_METRICS] = loadBool("feat_curveMetrics", true);
        enabled[FEAT_SPARKLINES] = loadBool("feat_sparklines", true);
        enabled[FEAT_DARK_MODE] = loadBool("feat_darkMode", false);
        enabled[FEAT_AUTO_THRESHOLD] = loadBool("feat_autoThreshold", false);
        enabled[FEAT_RADAR_ALERTS] = loadBool("feat_radarAlerts", true);
        enabled[FEAT_ALERT_SOUND] = loadBool("feat_alertSound", true);

        var m = Application.Storage.getValue("logMode");
        if (m != null && m >= 0 && m < LOG_COUNT) {
            logMode = m;
        } else {
            // Settings from before the single log mode: four toggles, of
            // which only the first enabled in this order was recorded
            if (loadBool("feat_hfreqAccel", false)) {
                logMode = LOG_HF;
            } else if (loadBool("feat_accelLog", false)) {
                logMode = LOG_ACCEL;
            } else if (loadBool("feat_rowingLog", true)) {
                logMode = LOG_ROWING;
            } else if (loadBool("feat_radarLog", false)) {
                logMode = LOG_RADAR;
            } else {
                logMode = LOG_OFF;
            }
        }
    }

    function loadBool(key, defaultVal) {
        var v = Application.Storage.getValue(key);
        return (v != null) ? v : defaultVal;
    }

    function isEnabled(featId) {
        switch (featId) {
            case FEAT_ROWING_LOG: return logMode == LOG_ROWING;
            case FEAT_HFREQ_ACCEL: return logMode == LOG_HF;
            case FEAT_ACCEL_LOG: return logMode == LOG_ACCEL;
            case FEAT_RADAR_LOG: return logMode == LOG_RADAR;
            default: return enabled[featId];
        }
    }

    function toggle(featId) {
        if (KEYS[featId] == null) { return; }
        enabled[featId] = !enabled[featId];
        Application.Storage.setValue(KEYS[featId], enabled[featId]);
    }

    function setLogMode(m) {
        logMode = m;
        Application.Storage.setValue("logMode", m);
    }

    static function getLogLabel(m) {
        switch (m) {
            case LOG_ROWING: return "Rowing Metrics";
            case LOG_HF: return "HF Accel 25 Hz";
            case LOG_ACCEL: return "Accel 1 Hz";
            case LOG_RADAR: return "Radar Targets";
            default: return "Off";
        }
    }

    static function getLogDescription(m) {
        switch (m) {
            case LOG_ROWING: return "Per-stroke metrics";
            case LOG_HF: return "Stroke signal, analysis";
            case LOG_ACCEL: return "Accel statistics";
            case LOG_RADAR: return "8 ranges and speeds";
            default: return "Rate and distance only";
        }
    }
}
