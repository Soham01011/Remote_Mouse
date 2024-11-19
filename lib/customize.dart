import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';

class PreferencePage extends StatefulWidget {
  @override
  _PreferencePageState createState() => _PreferencePageState();
}

class _PreferencePageState extends State<PreferencePage> {
  Map<String, Map<String, dynamic>> addedButtons = {};
  double joystickX1 = 0.1, joystickY1 = 0.6; // WASD Joystick Position
  double joystickX2 = 0.8, joystickY2 = 0.6; // Mouse Movement Joystick Position

  // Function to get the file path for storing preferences
  Future<String> getPreferencesFilePath() async {
    final directory = await getApplicationDocumentsDirectory();
    return '${directory.path}/preferences.json';
  }

  // Function to save layout positions to a JSON file
  Future<void> savePreferencesToFile() async {
    final filePath = await getPreferencesFilePath();

    // Create a map with all preferences
    Map<String, dynamic> preferences = {
      "joystick1": {"x": joystickX1, "y": joystickY1},
      "joystick2": {"x": joystickX2, "y": joystickY2},
      "buttons": addedButtons,
    };

    // Write the JSON data to the file
    final file = File(filePath);
    await file.writeAsString(jsonEncode(preferences));

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Preferences saved successfully!')),
    );
  }

  // Function to load preferences from a JSON file
  Future<void> loadPreferencesFromFile() async {
    final filePath = await getPreferencesFilePath();
    final file = File(filePath);

    if (await file.exists()) {
      final contents = await file.readAsString();
      final data = jsonDecode(contents);

      setState(() {
        joystickX1 = data["joystick1"]["x"];
        joystickY1 = data["joystick1"]["y"];
        joystickX2 = data["joystick2"]["x"];
        joystickY2 = data["joystick2"]["y"];
        addedButtons = Map<String, Map<String, dynamic>>.from(data["buttons"]);
      });
    } else {
      print('Preferences file does not exist. Using default settings.');
    }
  }

  @override
  void initState() {
    super.initState();
    loadPreferencesFromFile();
  }

  // Function to display joystick
  Widget buildJoystick(double x, double y, int joystickNumber) {
    return Positioned(
      left: x * MediaQuery.of(context).size.width,
      top: y * MediaQuery.of(context).size.height,
      child: GestureDetector(
        onPanUpdate: (details) {
          setState(() {
            double newX = (details.localPosition.dx / MediaQuery.of(context).size.width).clamp(0.0, 1.0);
            double newY = (details.localPosition.dy / MediaQuery.of(context).size.height).clamp(0.0, 1.0);
            if (joystickNumber == 1) {
              joystickX1 = newX;
              joystickY1 = newY;
            } else {
              joystickX2 = newX;
              joystickY2 = newY;
            }
          });
        },
        child: CircleAvatar(
          radius: 40,
          backgroundColor: Colors.green,
          child: Icon(Icons.gamepad, color: Colors.white),
        ),
      ),
    );
  }

  // Widget to display added buttons with movable feature
  Widget buildAddedButtons() {
    return Stack(
      children: addedButtons.entries.map((entry) {
        String label = entry.key;
        Map<String, dynamic> config = entry.value;
        double x = config["x"]!;
        double y = config["y"]!;
        bool isHoldDown = config["isHoldDown"]!;

        return Positioned(
          left: x * MediaQuery.of(context).size.width,
          top: y * MediaQuery.of(context).size.height,
          child: GestureDetector(
            onPanUpdate: (details) {
              setState(() {
                double newX = (details.localPosition.dx / MediaQuery.of(context).size.width).clamp(0.0, 1.0);
                double newY = (details.localPosition.dy / MediaQuery.of(context).size.height).clamp(0.0, 1.0);
                addedButtons[label]!["x"] = newX;
                addedButtons[label]!["y"] = newY;
              });
            },
            onLongPress: () => showDeleteButtonDialog(label),
            child: CircleAvatar(
              radius: 30,
              backgroundColor: Colors.blue,
              child: Text(
                label,
                style: TextStyle(color: Colors.white),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  // Function to show delete button confirmation dialog
  void showDeleteButtonDialog(String label) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Delete Button'),
          content: Text('Are you sure you want to delete the button "$label"?'),
          actions: [
            TextButton(
              child: Text('Cancel'),
              onPressed: () => Navigator.of(context).pop(),
            ),
            TextButton(
              child: Text('Delete'),
              onPressed: () {
                setState(() {
                  addedButtons.remove(label);
                });
                Navigator.of(context).pop();
              },
            ),
          ],
        );
      },
    );
  }

  // Function to show the Add Button dialog
  void showAddButtonDialog() {
    String label = '';
    bool isHoldDown = false;
    double x = 0.5;
    double y = 0.5;

    showDialog(
      context: context,
      builder: (BuildContext context) {
        return StatefulBuilder(
          builder: (context, dialogSetState) {
            return AlertDialog(
              title: Text('Add Button'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      decoration: InputDecoration(labelText: 'Button Label'),
                      onChanged: (value) {
                        label = value;
                      },
                    ),
                    Row(
                      children: [
                        Text('Hold Down'),
                        Switch(
                          value: isHoldDown,
                          onChanged: (value) {
                            dialogSetState(() {
                              isHoldDown = value;
                            });
                          },
                        ),
                      ],
                    ),
                    TextField(
                      decoration: InputDecoration(labelText: 'X Position (0-1)'),
                      keyboardType: TextInputType.number,
                      onChanged: (value) {
                        x = double.tryParse(value) ?? 0.5;
                      },
                    ),
                    TextField(
                      decoration: InputDecoration(labelText: 'Y Position (0-1)'),
                      keyboardType: TextInputType.number,
                      onChanged: (value) {
                        y = double.tryParse(value) ?? 0.5;
                      },
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  child: Text('Cancel'),
                  onPressed: () => Navigator.of(context).pop(),
                ),
                TextButton(
                  child: Text('Add'),
                  onPressed: () {
                    if (label.isNotEmpty && x >= 0 && x <= 1 && y >= 0 && y <= 1) {
                      addButton(label, isHoldDown, x, y);
                      Navigator.of(context).pop();
                    }
                  },
                ),
              ],
            );
          },
        );
      },
    );
  }

  // Function to add a button to the layout
  void addButton(String label, bool isHoldDown, double x, double y) {
    setState(() {
      addedButtons[label] = {
        "label": label,
        "isHoldDown": isHoldDown,
        "x": x,
        "y": y,
      };
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Preferences'),
        actions: [
          IconButton(
            icon: Icon(Icons.save),
            onPressed: savePreferencesToFile, // Save layout to file
          ),
        ],
      ),
      body: Stack(
        children: [
          buildAddedButtons(),
          buildJoystick(joystickX1, joystickY1, 1), // WASD Joystick
          buildJoystick(joystickX2, joystickY2, 2), // Mouse Movement Joystick
          Align(
            alignment: Alignment.bottomRight,
            child: FloatingActionButton(
              child: Icon(Icons.add),
              onPressed: showAddButtonDialog,
            ),
          ),
        ],
      ),
    );
  }
}