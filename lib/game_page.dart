import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_joystick/flutter_joystick.dart';
import 'package:path_provider/path_provider.dart';
import 'package:web_socket_channel/io.dart';
import 'customize.dart';
import 'dart:math';

class GamingModePage extends StatefulWidget {
  final String ipAddress;

  GamingModePage({required this.ipAddress});

  @override
  _GamingModePageState createState() => _GamingModePageState();
}

class _GamingModePageState extends State<GamingModePage> {
  late IOWebSocketChannel joystickChannel; // WASD Joystick
  late IOWebSocketChannel mouseChannel; // Mouse Movement
  late IOWebSocketChannel buttonChannel; // Button Presses

  Map<String, Map<String, dynamic>> layoutData = {};
  Offset joystick1Offset = Offset(0.1, 0.6); // WASD Joystick
  Offset joystick2Offset = Offset(0.8, 0.6); // Mouse Movement Joystick
  double mouseSensitivity = 50;

  @override
  void initState() {
    super.initState();
    _setLandscapeAndFullscreen();

    // Initialize WebSocket channels for joystick, mouse, and button press
    joystickChannel = IOWebSocketChannel.connect('ws://${widget.ipAddress}:9999/joystick');
    mouseChannel = IOWebSocketChannel.connect('ws://${widget.ipAddress}:9998/mousemovement');
    buttonChannel = IOWebSocketChannel.connect('ws://${widget.ipAddress}:9997/buttonpress'); // New route for button press

    loadPreferences();
  }

  void _setLandscapeAndFullscreen() {
    SystemChrome.setPreferredOrientations([DeviceOrientation.landscapeRight, DeviceOrientation.landscapeLeft]);
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  }

  Future<void> loadPreferences() async {
    final directory = await getApplicationDocumentsDirectory();
    final filePath = '${directory.path}/preferences.json';
    final file = File(filePath);

    if (await file.exists()) {
      final contents = await file.readAsString();
      final data = jsonDecode(contents);

      setState(() {
        layoutData = Map<String, Map<String, dynamic>>.from(data["buttons"]);
        joystick1Offset = Offset(data["joystick1"]["x"], data["joystick1"]["y"]);
        joystick2Offset = Offset(data["joystick2"]["x"], data["joystick2"]["y"]);
      });

      print("Layout loaded: $layoutData");
    } else {
      print("No preferences file found. Using default layout.");
    }
  }

  String mapJoystickToDirection(double x, double y) {
    // Calculate the angle in degrees
    double angle = atan2(-y, x) * 180 / pi; // -y because up is negative
    angle = (angle + 360) % 360; // Normalize angle to 0-360 degrees

    // Determine the sector
    if (angle >= 337.5 || angle < 22.5) {
      return "D"; // Right
    } else if (angle >= 22.5 && angle < 67.5) {
      return "WD"; // Up-Right
    } else if (angle >= 67.5 && angle < 112.5) {
      return "W"; // Up
    } else if (angle >= 112.5 && angle < 157.5) {
      return "WA"; // Up-Left
    } else if (angle >= 157.5 && angle < 202.5) {
      return "A"; // Left
    } else if (angle >= 202.5 && angle < 247.5) {
      return "SA"; // Down-Left
    } else if (angle >= 247.5 && angle < 292.5) {
      return "S"; // Down
    } else if (angle >= 292.5 && angle < 337.5) {
      return "SD"; // Down-Right
    } else {
      return "CENTER"; // Default case
    }
  }

  // Send data to the appropriate WebSocket channel
  void sendKeyData(Map<String, dynamic> data, {required String channelType}) {
    try {
      IOWebSocketChannel channel;

      // Choose the correct channel based on input type
      switch (channelType) {
        case 'joystick':
          channel = joystickChannel;
          break;
        case 'mouse':
          channel = mouseChannel;
          break;
        case 'button':
          channel = buttonChannel;
          break;
        default:
          return;
      }

      channel.sink.add(json.encode(data));
      print('Data sent ($channelType): $data');
    } catch (e) {
      print('Error sending data ($channelType): $e');
    }
  }

  @override
  void dispose() {
    joystickChannel.sink.close();
    mouseChannel.sink.close();
    buttonChannel.sink.close();
    SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp, DeviceOrientation.portraitDown]);
    super.dispose();
  }

  Widget buildJoystick(Offset offset, String joystickType, {double sensitivity = 1.0}) {
    return Positioned(
      left: offset.dx * MediaQuery.of(context).size.width,
      top: offset.dy * MediaQuery.of(context).size.height,
      child: Joystick(
        mode: JoystickMode.all, // Allows movement in all directions
        listener: (details) {
          final dx = details.x * sensitivity;
          final dy = details.y * sensitivity;

          if (dx == 0 && dy == 0) {
            // Joystick released (centered position)
            if (joystickType == "WASD") {
              sendKeyData({
                "joystickType": joystickType,
                "direction": "", // No movement
              }, channelType: 'joystick');
              print('$joystickType Joystick Released');
            } else if (joystickType == "Mouse") {
              sendKeyData({
                "joystickType": joystickType,
                "x": 0,
                "y": 0, // Stop mouse movement
              }, channelType: 'mouse');
              print('$joystickType Joystick Stopped');
            }
          } else {
            // Joystick active
            if (joystickType == "WASD") {
              String direction = mapJoystickToDirection(dx, dy);
              sendKeyData({
                "joystickType": joystickType,
                "direction": direction,
              }, channelType: 'joystick');
              print('$joystickType Joystick - Direction: $direction');
            } else if (joystickType == "Mouse") {
              sendKeyData({
                "joystickType": joystickType,
                "x": dx,
                "y": dy,
              }, channelType: 'mouse');
              print('$joystickType Joystick - X: $dx, Y: $dy');
            }
          }
        },
      ),
    );
  }

  Widget buildButtons() {
    return Stack(
      children: layoutData.entries.map((entry) {
        String label = entry.key;
        Map<String, dynamic> config = entry.value;
        Offset buttonOffset = Offset(config["x"], config["y"]);

        // Initialize a state variable to track the current state of the button
        bool isHeld = false;

        return Positioned(
          left: buttonOffset.dx * MediaQuery.of(context).size.width,
          top: buttonOffset.dy * MediaQuery.of(context).size.height,
          child: GestureDetector(
            onTap: () {
              // Single tap: "pressed" state
              sendKeyData({
                "button": label,
                "state": "pressed",
              }, channelType: 'button');
              print('Button "$label" single-tapped, state: pressed');
            },
            onDoubleTap: () {
              // Double tap: Toggle between "held" and "released" states
              String state = isHeld ? "released" : "held";
              isHeld = !isHeld; // Toggle the state
              sendKeyData({
                "button": label,
                "state": state,
              }, channelType: 'button');
              print('Button "$label" double-tapped, state: $state');
            },
            onLongPress: () {
              // Long press: Set to "held" state
              if (!isHeld) {
                isHeld = true;
                sendKeyData({
                  "button": label,
                  "state": "held",
                }, channelType: 'button');
                print('Button "$label" long-pressed, state: held');
              }
            },
            onLongPressUp: () {
              // Long press released: Set to "released" state
              if (isHeld) {
                isHeld = false;
                sendKeyData({
                  "button": label,
                  "state": "released",
                }, channelType: 'button');
                print('Button "$label" long-press released, state: released');
              }
            },
            child: CircleAvatar(
              radius: 30,
              backgroundColor: isHeld ? Colors.blue : Colors.red, // Change to blue if held
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar:AppBar(
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Gaming Mode'),
            Row(
              children: [
                Text(
                  'Mouse Sensitivity:',
                  style: TextStyle(fontSize: 16),
                ),
                SizedBox(width: 8),
                Container(
                  width: 60, // Adjust input width
                  child: TextField(
                    keyboardType: TextInputType.number,
                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                    onSubmitted: (value) {
                      setState(() {
                        // Parse sensitivity directly as input (no modifications)
                        mouseSensitivity = double.tryParse(value) ?? 50; // Default to 50 if parsing fails
                        print("Mouse sensitivity set to: $mouseSensitivity");
                      });
                      // Send updated sensitivity to the server
                      sendKeyData({
                        "joystickType": "Mouse",
                        "sensitivity": mouseSensitivity,
                      }, channelType: 'mouse');
                    },
                    decoration: InputDecoration(
                      hintText: "0-100",
                      contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 0),
                      border: OutlineInputBorder(),
                      isDense: true, // Compact appearance
                    ),
                  ),
                ),
              ],
            ),
            IconButton(
              icon: Icon(Icons.settings),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => PreferencePage()),
                ).then((_) => loadPreferences());
              },
            ),
          ],
        ),
      ),
      body: Stack(
        children: [
          buildJoystick(joystick1Offset, "WASD"), // WASD joystick
          buildJoystick(joystick2Offset, "Mouse", sensitivity: 1.5), // Mouse joystick
          buildButtons(), // Configurable buttons
        ],
      ),
    );
  }
}
