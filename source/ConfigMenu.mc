using Toybox.WatchUi;
using Toybox.Graphics;
using Toybox.Application;
using Toybox.System;

// Settings menu, grouped by what the rower is doing:
//   Data Fields, Zoom Level         - the data screen, changed often
//   Stroke Detection                - threshold, changed with the boat
//   Display, Radar                  - set once
//   Recording                       - auto pause, what the FIT file holds
//   Demo Mode                       - testing only
// Each entry shows its current state in the second line.

// Second-line texts, shared by the menus and refreshed when they reappear
class SettingsText {
    static function zoom() {
        var cfg = Application.getApp().fieldConfig;
        var ds = System.getDeviceSettings();
        var n = (ds.screenHeight > 400) ? cfg.getVisibleCountTall() : cfg.getVisibleCount();
        return "z" + cfg.zoomLevel + " (" + n + " fields)";
    }

    static function threshold() {
        return Application.getApp().strokeDetector.catchThreshold.toNumber() + " mG";
    }

    static function detection() {
        var fc = Application.getApp().featureConfig;
        if (fc.isEnabled(FeatureConfig.FEAT_AUTO_THRESHOLD)) {
            return "Auto, from " + threshold();
        }
        return "Manual, " + threshold();
    }

    static function display() {
        var fc = Application.getApp().featureConfig;
        var s = fc.isEnabled(FeatureConfig.FEAT_DARK_MODE) ? "Dark" : "Light";
        if (fc.isEnabled(FeatureConfig.FEAT_SPARKLINES)) { s += ", sparklines"; }
        return s;
    }

    static function radar() {
        var fc = Application.getApp().featureConfig;
        if (!fc.isEnabled(FeatureConfig.FEAT_RADAR_ALERTS)) { return "Alerts off"; }
        return fc.isEnabled(FeatureConfig.FEAT_ALERT_SOUND) ? "Alerts with sound" : "Alerts, no sound";
    }

    static function recording() {
        var fc = Application.getApp().featureConfig;
        var s = fc.isEnabled(FeatureConfig.FEAT_AUTO_PAUSE) ? "Auto pause, " : "";
        return s + FeatureConfig.getLogLabel(fc.logMode);
    }
}

// Set the second line of the item with this id, if the menu has it
function setSub(menu, id, text) {
    var i = menu.findItemById(id);
    if (i >= 0) {
        var item = menu.getItem(i);
        item.setSubLabel(text);
        menu.updateItem(item, i);
    }
}

function toggleItem(label, sub, featId) {
    return new WatchUi.ToggleMenuItem(label, sub, featId,
        Application.getApp().featureConfig.isEnabled(featId), null);
}

// Main settings menu
class MainMenuView extends WatchUi.Menu2 {
    function initialize() {
        Menu2.initialize({:title => "Settings"});
        addItem(new WatchUi.MenuItem("Data Fields", "Order and choice", :dataFields, null));
        addItem(new WatchUi.MenuItem("Zoom Level", SettingsText.zoom(), :zoom, null));
        addItem(new WatchUi.MenuItem("Stroke Detection", SettingsText.detection(), :detection, null));
        addItem(new WatchUi.MenuItem("Display", SettingsText.display(), :display, null));
        addItem(new WatchUi.MenuItem("Radar", SettingsText.radar(), :radar, null));
        addItem(new WatchUi.MenuItem("Recording", SettingsText.recording(), :recording, null));
        addItem(toggleItem("Demo Mode", "Replay of recorded strokes", FeatureConfig.FEAT_DEMO_MODE));
    }

    function onShow() {
        Menu2.onShow();
        setSub(self, :zoom, SettingsText.zoom());
        setSub(self, :detection, SettingsText.detection());
        setSub(self, :display, SettingsText.display());
        setSub(self, :radar, SettingsText.radar());
        setSub(self, :recording, SettingsText.recording());
    }
}

class MainMenuDelegate extends WatchUi.Menu2InputDelegate {
    function initialize() {
        Menu2InputDelegate.initialize();
    }

    function onSelect(item) {
        var id = item.getId();
        if (id == :dataFields) {
            WatchUi.pushView(new FieldListMenu(), new FieldListMenuDelegate(), WatchUi.SLIDE_LEFT);
        } else if (id == :zoom) {
            WatchUi.pushView(new ZoomMenu(), new ZoomMenuDelegate(), WatchUi.SLIDE_LEFT);
        } else if (id == :detection) {
            WatchUi.pushView(new DetectionMenu(), new DetectionMenuDelegate(), WatchUi.SLIDE_LEFT);
        } else if (id == :display) {
            WatchUi.pushView(new DisplayMenu(), new ToggleOnlyDelegate(), WatchUi.SLIDE_LEFT);
        } else if (id == :radar) {
            WatchUi.pushView(new RadarMenu(), new ToggleOnlyDelegate(), WatchUi.SLIDE_LEFT);
        } else if (id == :recording) {
            WatchUi.pushView(new RecordingMenu(), new RecordingMenuDelegate(), WatchUi.SLIDE_LEFT);
        } else if (id == FeatureConfig.FEAT_DEMO_MODE) {
            Application.getApp().featureConfig.toggle(id);
        }
    }
}

// Stroke Detection: automatic or manual threshold
class DetectionMenu extends WatchUi.Menu2 {
    function initialize() {
        Menu2.initialize({:title => "Stroke Detection"});
        addItem(toggleItem("Auto Threshold", "Adapts to boat and rowing", FeatureConfig.FEAT_AUTO_THRESHOLD));
        addItem(new WatchUi.MenuItem("Threshold", SettingsText.threshold(), :threshold, null));
    }

    function onShow() {
        Menu2.onShow();
        setSub(self, :threshold, SettingsText.threshold());
    }
}

class DetectionMenuDelegate extends WatchUi.Menu2InputDelegate {
    function initialize() {
        Menu2InputDelegate.initialize();
    }

    function onSelect(item) {
        var id = item.getId();
        if (id == :threshold) {
            WatchUi.pushView(new ThresholdPicker(), new ThresholdPickerDelegate(), WatchUi.SLIDE_LEFT);
        } else {
            Application.getApp().featureConfig.toggle(id);
        }
    }
}

// Display: theme and what is drawn on the data screen
class DisplayMenu extends WatchUi.Menu2 {
    function initialize() {
        Menu2.initialize({:title => "Display"});
        addItem(toggleItem("Dark Mode", "Black background", FeatureConfig.FEAT_DARK_MODE));
        addItem(toggleItem("Sparkline Graphs", "60 s history, main fields", FeatureConfig.FEAT_SPARKLINES));
        addItem(toggleItem("Curve Metrics", "FR% and delta-V on curve", FeatureConfig.FEAT_CURVE_METRICS));
    }
}

// Radar: obstacle alerts from a Varia radar
class RadarMenu extends WatchUi.Menu2 {
    function initialize() {
        Menu2.initialize({:title => "Radar"});
        addItem(toggleItem("Obstacle Alerts", "Warning bar and alerts", FeatureConfig.FEAT_RADAR_ALERTS));
        addItem(toggleItem("Alert Sound", "Tone on warnings", FeatureConfig.FEAT_ALERT_SOUND));
    }
}

// Menus made only of feature toggles
class ToggleOnlyDelegate extends WatchUi.Menu2InputDelegate {
    function initialize() {
        Menu2InputDelegate.initialize();
    }

    function onSelect(item) {
        Application.getApp().featureConfig.toggle(item.getId());
    }
}

// Recording: auto pause and what the FIT file records
class RecordingMenu extends WatchUi.Menu2 {
    function initialize() {
        Menu2.initialize({:title => "Recording"});
        addItem(toggleItem("Auto Pause", "When the boat stops", FeatureConfig.FEAT_AUTO_PAUSE));
        var fc = Application.getApp().featureConfig;
        addItem(new WatchUi.MenuItem("FIT Log", FeatureConfig.getLogLabel(fc.logMode), :fitLog, null));
    }

    function onShow() {
        Menu2.onShow();
        setSub(self, :fitLog, FeatureConfig.getLogLabel(Application.getApp().featureConfig.logMode));
    }
}

class RecordingMenuDelegate extends WatchUi.Menu2InputDelegate {
    function initialize() {
        Menu2InputDelegate.initialize();
    }

    function onSelect(item) {
        var id = item.getId();
        if (id == :fitLog) {
            WatchUi.pushView(new LogModeMenu(), new LogModeMenuDelegate(), WatchUi.SLIDE_LEFT);
        } else {
            Application.getApp().featureConfig.toggle(id);
        }
    }
}

// FIT Log: one choice, the current one is focused and marked
class LogModeMenu extends WatchUi.Menu2 {
    function initialize() {
        var current = Application.getApp().featureConfig.logMode;
        var order = [FeatureConfig.LOG_ROWING, FeatureConfig.LOG_HF, FeatureConfig.LOG_ACCEL,
                     FeatureConfig.LOG_RADAR, FeatureConfig.LOG_OFF];
        var focus = 0;
        for (var i = 0; i < order.size(); i++) {
            if (order[i] == current) { focus = i; }
        }
        Menu2.initialize({:title => "FIT Log", :focus => focus});
        for (var i = 0; i < order.size(); i++) {
            var m = order[i];
            var label = FeatureConfig.getLogLabel(m);
            if (m == current) { label = "* " + label; }
            addItem(new WatchUi.MenuItem(label, FeatureConfig.getLogDescription(m), m, null));
        }
    }
}

class LogModeMenuDelegate extends WatchUi.Menu2InputDelegate {
    function initialize() {
        Menu2InputDelegate.initialize();
    }

    function onSelect(item) {
        Application.getApp().featureConfig.setLogMode(item.getId());
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
    }
}

// Field list menu: shows ordered fields, select one to edit/move/remove
class FieldListMenu extends WatchUi.Menu2 {
    function initialize() {
        Menu2.initialize({:title => "Data Fields"});
        rebuildItems();
    }

    function rebuildItems() {
        // Clear existing
        while (getItem(0) != null) {
            deleteItem(0);
        }

        var app = Application.getApp();
        var cfg = app.fieldConfig;
        for (var i = 0; i < cfg.fields.size(); i++) {
            var fid = cfg.fields[i];
            var pos = (i + 1).format("%d");
            var visCount = cfg.getVisibleCount();
            addItem(new WatchUi.MenuItem(
                pos + ". " + FieldConfig.getMenuLabel(fid),
                i < visCount ? "visible" : "hidden",
                i,  // use index as item ID
                null
            ));
        }
        // Add field option
        addItem(new WatchUi.MenuItem("+ Add Field", null, :addField, null));
    }
}

class FieldListMenuDelegate extends WatchUi.Menu2InputDelegate {
    function initialize() {
        Menu2InputDelegate.initialize();
    }

    function onSelect(item) {
        var id = item.getId();
        if (id == :addField) {
            WatchUi.pushView(
                new AddFieldMenu(),
                new AddFieldMenuDelegate(),
                WatchUi.SLIDE_LEFT
            );
        } else {
            // id is field index -- show edit menu for this field
            WatchUi.pushView(
                new FieldEditMenu(id),
                new FieldEditMenuDelegate(id),
                WatchUi.SLIDE_LEFT
            );
        }
    }
}

// Edit a single field: Move Up, Move Down, Remove
class FieldEditMenu extends WatchUi.Menu2 {
    function initialize(index) {
        var app = Application.getApp();
        var fid = app.fieldConfig.fields[index];
        Menu2.initialize({:title => FieldConfig.getMenuLabel(fid)});

        if (index > 0) {
            addItem(new WatchUi.MenuItem("Move to Top", null, :moveTop, null));
            addItem(new WatchUi.MenuItem("Move Up", null, :moveUp, null));
        }
        if (index < app.fieldConfig.fields.size() - 1) {
            addItem(new WatchUi.MenuItem("Move Down", null, :moveDown, null));
        }
        if (app.fieldConfig.fields.size() > 2) {
            addItem(new WatchUi.MenuItem("Remove", null, :remove, null));
        }
    }
}

class FieldEditMenuDelegate extends WatchUi.Menu2InputDelegate {
    var fieldIndex;

    function initialize(index) {
        Menu2InputDelegate.initialize();
        fieldIndex = index;
    }

    function onSelect(item) {
        var app = Application.getApp();
        var cfg = app.fieldConfig;
        var id = item.getId();

        if (id == :moveTop) {
            cfg.moveTop(fieldIndex);
        } else if (id == :moveUp) {
            cfg.moveUp(fieldIndex);
        } else if (id == :moveDown) {
            cfg.moveDown(fieldIndex);
        } else if (id == :remove) {
            cfg.removeField(fieldIndex);
        }

        // Pop back to field list and rebuild
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
        WatchUi.pushView(
            new FieldListMenu(),
            new FieldListMenuDelegate(),
            WatchUi.SLIDE_LEFT
        );
    }
}

// Add field menu: shows fields not yet in the list
class AddFieldMenu extends WatchUi.Menu2 {
    function initialize() {
        Menu2.initialize({:title => "Add Field"});
        var app = Application.getApp();
        var cfg = app.fieldConfig;

        for (var fid = 0; fid < FieldConfig.F_COUNT; fid++) {
            // Skip if already in list
            var found = false;
            for (var j = 0; j < cfg.fields.size(); j++) {
                if (cfg.fields[j] == fid) { found = true; break; }
            }
            if (!found) {
                addItem(new WatchUi.MenuItem(
                    FieldConfig.getMenuLabel(fid), null, fid, null
                ));
            }
        }
    }
}

class AddFieldMenuDelegate extends WatchUi.Menu2InputDelegate {
    function initialize() {
        Menu2InputDelegate.initialize();
    }

    function onSelect(item) {
        var fid = item.getId();
        var app = Application.getApp();
        app.fieldConfig.addField(fid);

        // Pop back to field list and rebuild
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
        WatchUi.pushView(
            new FieldListMenu(),
            new FieldListMenuDelegate(),
            WatchUi.SLIDE_LEFT
        );
    }
}

// Zoom level selection: Menu2 list (touch-friendly)
class ZoomMenu extends WatchUi.Menu2 {
    function initialize() {
        Menu2.initialize({:title => "Zoom Level"});
        var app = Application.getApp();
        var current = app.fieldConfig.zoomLevel;
        // Use tall counts on tall screens (detected via System.getDeviceSettings)
        var ds = System.getDeviceSettings();
        var tall = (ds.screenHeight > 400);
        var counts = tall ? FieldConfig.ZOOM_FIELD_COUNT_TALL : FieldConfig.ZOOM_FIELD_COUNT;
        for (var z = 1; z <= 7; z++) {
            var label = "z" + z + " - " + counts[z] + " fields";
            var sub = (z == current) ? "current" : null;
            addItem(new WatchUi.MenuItem(label, sub, z, null));
        }
    }
}

class ZoomMenuDelegate extends WatchUi.Menu2InputDelegate {
    function initialize() {
        Menu2InputDelegate.initialize();
    }

    function onSelect(item) {
        var z = item.getId();
        var app = Application.getApp();
        var cfg = app.fieldConfig;
        cfg.zoomLevel = z;
        cfg.save();
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
    }
}
