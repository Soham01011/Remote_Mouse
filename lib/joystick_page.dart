import 'dart:async';
import 'dart:convert';
import 'seamless_page.dart';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/io.dart';
import 'package:remote_mouse_v2/game_page.dart';
import 'package:flutter_joystick/flutter_joystick.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class JoystickPage extends StatefulWidget {
  final String ipAddress;

  // Modify the constructor to accept the ipAddress
  JoystickPage({required this.ipAddress});

  @override
  _JoyStickPage createState() => _JoyStickPage();
}

class _JoyStickPage extends State<JoystickPage> {
  final TextEditingController _sensitivityController = TextEditingController(text: '15');
  WebSocketChannel? generalChannel;
  WebSocketChannel? mouseChannel;
  WebSocketChannel? appChannel;
  bool isConnected = true;
  bool hotShift = false;
  bool hotCtrl = false;
  bool hotAlt = false;
  bool hotTab = false;
  bool hotEsc = false;
  bool hotEnter = false;
  bool hotDel = false;
  bool hotIns = false;
  bool hotNumLock = false;
  bool leftButtonPressed = false;
  double sensitivity = 15;
  double previousDx = 0;
  double previousDy = 0;
  double _mainPanelHeight = 80;
  double _trackPanelHeight = 0;
  double _keyBoardPanelHeight = 0;
  double _appPanelHeight = 0;
  double _mousePanelHeight = 0;
  double _webPanelHeight = 0;
  double _quickPanelHeight = 0;
  double _filePanelHeight = 0;
  List<dynamic> runningApps = [];
  List<Map<String, dynamic>> directoryContents = [];
  String currentDirectory = "";
  Timer? _tapTimer;
  String errorMessage = '';
  String scannedData = '';

  void togglefliePanel() {
    setState(() {
      if (_filePanelHeight == 0.2) {
        _mainPanelHeight = 80;
        _filePanelHeight = 0;
      }
      else {
        _mainPanelHeight = 0;
        _filePanelHeight = 0.2;
      }
    });
  }

  void toggleTrackPanel() {
    setState(() {
      if (_trackPanelHeight == 0.2) {
        _mainPanelHeight = 80;
        _trackPanelHeight = 0;
      }
      else {
        _mainPanelHeight = 0;
        _trackPanelHeight = 0.2;
      }
    });
  }

  void toggleKeyboardPanel() {
    setState(() {
      if (_keyBoardPanelHeight == 0.2) {
        _mainPanelHeight = 80;
        _keyBoardPanelHeight = 0;
      }
      else {
        _mainPanelHeight = 0;
        _keyBoardPanelHeight = 0.2;
      }
    });
  }

  void toggleAppPanel() {
    setState(() {
      if (_appPanelHeight == 0.3) {
        _mainPanelHeight = 80;
        _appPanelHeight = 0;
      } else {
        _mainPanelHeight = 0;
        _appPanelHeight = 0.3;
        appChannel!.sink.add('GET_RUNNING_APPS');
      }
    });
  }


  void toggleMousePanel() {
    setState(() {
      if (_mousePanelHeight == 0.2) {
        _mainPanelHeight = 80;
        _mousePanelHeight = 0;
      }
      else {
        _mousePanelHeight = 0.2;
        _mainPanelHeight = 0;
      }
    });
  }

  void toggleWebPanel() {
    setState(() {
      if (_webPanelHeight == 0.2) {
        _mainPanelHeight = 80;
        _webPanelHeight = 0;
      }
      else {
        _webPanelHeight = 0.2;
        _mainPanelHeight = 0;
      }
    });
  }

  void toggleQuickLaunch() {
    setState(() {
      if (_quickPanelHeight == 0.2) {
        _mainPanelHeight = 80;
        _quickPanelHeight = 0;
      }
      else {
        _quickPanelHeight = 0.2;
        _mainPanelHeight = 0;
      }
    });
  }
  void focusApp(String appName) {
    if (generalChannel != null) {
      generalChannel!.sink.add("FOCUS_APP,$appName,open");
    }
  }

  void opencloseApp(String appName) {
    // Debounce single tap to check if it's a double tap
    if (_tapTimer != null && _tapTimer!.isActive) {
      _tapTimer!.cancel();
      if (generalChannel != null) {
        generalChannel!.sink.add("FOCUS_APP,$appName,close");
      }
    } else {
      _tapTimer = Timer(Duration(milliseconds: 300), () => focusApp(appName));
    }
  }



  void fetchRunningApps() {
    if (appChannel != null) {
      sendCommand({"command": "GET_RUNNING_APPS"});
    }
  }


  void hotKey(String hotkey) {
    switch (hotkey) {
      case "SHIFT":
        setState(() {
          hotShift = !hotShift;
        });
        sendGeneralCommand(hotShift ? "SHIFT_DOWN" : "SHIFT_UP");
        break;
      case "CTRL":
        setState(() {
          hotCtrl = !hotCtrl;
        });
        sendGeneralCommand(hotCtrl ? "CTRL_DOWN" : "CTRL_UP");
        break;
      case "TAB":
        setState(() {
          hotTab = !hotTab;
        });
        sendGeneralCommand(hotTab ? "TAB_DOWN" : "TAB_UP");
        break;
      case "ESC":
        setState(() {
          hotEsc = !hotEsc;
        });
        sendGeneralCommand(hotEsc ? "ESC_DOWN" : "ESC_UP");
        break;
      case "ALT":
        setState(() {
          hotAlt = !hotAlt;
        });
        sendGeneralCommand(hotAlt ? "ALT_DOWN" : "ALT_UP");
        break;
    }
  }

  void _handleMouseClick() {
    sendGeneralCommand("LEFT_CLICK");
  }

  void _handleMouseDoubleClick() {
    if (leftButtonPressed) {
      // If click is held, release it
      sendGeneralCommand("LEFT_CLICK_UP");
      leftButtonPressed = false;
    } else {
      // If click is not held, hold it down
      sendGeneralCommand("LEFT_CLICK_DOWN");
      leftButtonPressed = true;
    }
  }

  void _handleTap() {
    // Debounce single tap to check if it's a double tap
    if (_tapTimer != null && _tapTimer!.isActive) {
      _tapTimer!.cancel();
      _handleMouseDoubleClick();
    } else {
      _tapTimer = Timer(Duration(milliseconds: 300), _handleMouseClick);
    }
  }


  void disconnectFromServer() {
    generalChannel?.sink.close();
    mouseChannel?.sink.close();
    appChannel?.sink.close();
    setState(() {
      isConnected = false;
    });
  }

  void sendGeneralCommand(String command) {
    if (generalChannel != null) {
      generalChannel!.sink.add(command);
    }
  }

  void sendMouseCommand(String command) {
    if (mouseChannel != null) {
      mouseChannel!.sink.add(command);
    }
  }

  void updateSensitivity() {
    setState(() {
      sensitivity = double.tryParse(_sensitivityController.text) ?? 15;
    });
  }



  void sendCommand(Map<String, dynamic> command) {

      String commandType = command["command"];
      if (commandType == "GET_RUNNING_APPS" && appChannel != null) {
        appChannel!.sink.add(jsonEncode(command));
      } else if (commandType.startsWith("MOUSE") && mouseChannel != null) {
        mouseChannel!.sink.add(jsonEncode(command));
      } else {
        print("Invalid command or channel not connected.");
      }

  }


  @override
  void initState() {
    super.initState();

    // Use the ipAddress from the widget to connect to WebSocket
    generalChannel = IOWebSocketChannel.connect('ws://${widget.ipAddress}:9999');
    mouseChannel = IOWebSocketChannel.connect('ws://${widget.ipAddress}:9998/mouse');
    appChannel = IOWebSocketChannel.connect('ws://${widget.ipAddress}:9997/apps');
    fetchRunningApps();
    appChannel!.stream.listen((message) {
      setState(() {
        var decodedMessage = jsonDecode(message);
        if (decodedMessage is List) {
          runningApps = List<Map<String, dynamic>>.from(decodedMessage);
          print("Running app form server : ${runningApps}");
        }
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Joystick Page'),
        actions: [
          IconButton(onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => SeamlessModePage(ipAddress: widget.ipAddress),
                  ),
            );
            },
              icon: Icon(Icons.screenshot_monitor)),
          IconButton(onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => GamingModePage(ipAddress: widget.ipAddress),
              ),
            );
          },
              icon: Icon(Icons.control_camera))
        ],
      ),
      body: Center(
        child: Column(
          children: [
            Expanded(
              child: Column(
                children: [
                  Expanded(
                    child: Center(
                      child: Joystick(
                        listener: (details) {
                          final dx = details.x * sensitivity;
                          final dy = details.y * sensitivity;
                          sendMouseCommand("MOUSE_MOVE,$dx,$dy");
                        },
                      ),
                    ),
                  ),
                  TextField(
                    controller: _sensitivityController,
                    decoration: InputDecoration(
                      labelText: 'Set your joystick sensitivity',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.number,
                    onSubmitted: (_) => updateSensitivity(),
                  ),
                  SizedBox(height: 10),
                  Container(
                    height: _mainPanelHeight,
                    child: ListView(
                      scrollDirection: Axis.horizontal,
                      children: [
                        IconButton(
                          icon: Icon(Icons.mouse),
                          onPressed: toggleMousePanel,
                        ),
                        IconButton(
                          icon: Icon(Icons.play_arrow),
                          onPressed: toggleTrackPanel,
                        ),
                        IconButton(
                          icon: Icon(Icons.keyboard),
                          onPressed: toggleKeyboardPanel,
                        ),
                        IconButton(
                          icon: Icon(Icons.apps),
                          onPressed: toggleAppPanel,
                        ),
                        IconButton(
                          icon: Icon(Icons.web),
                          onPressed: toggleWebPanel,
                        ),
                        IconButton(
                          icon: Icon(Icons.rocket_launch),
                          onPressed: toggleQuickLaunch,
                        ),
                        IconButton(
                          icon: Icon(Icons.file_open),
                          onPressed: togglefliePanel,
                        )
                      ],
                    ),
                  ),
                  Container(
                    height: MediaQuery
                        .of(context)
                        .size
                        .height * _trackPanelHeight,
                    color: Colors.grey[200],
                    child: Column(
                      children: [
                        IconButton(
                          icon: Icon(Icons.close),
                          onPressed: toggleTrackPanel,
                        ),
                        Spacer(),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          children: [
                            IconButton(
                              icon: Icon(Icons.skip_previous),
                              onPressed: () => sendGeneralCommand("PREV"),
                            ),
                            IconButton(
                              icon: Icon(Icons.play_arrow),
                              onPressed: () =>
                                  sendGeneralCommand("PLAY_PAUSE"),
                            ),
                            IconButton(
                              icon: Icon(Icons.skip_next),
                              onPressed: () => sendGeneralCommand("NEXT"),
                            ),
                            IconButton(
                              icon: Icon(Icons.volume_up),
                              onPressed: () =>
                                  sendGeneralCommand("VOLUME_UP"),
                            ),
                            IconButton(
                              icon: Icon(Icons.volume_down),
                              onPressed: () =>
                                  sendGeneralCommand("VOLUME_DOWN"),
                            ),
                            IconButton(
                              icon: Icon(Icons.volume_mute),
                              onPressed: () => sendGeneralCommand("MUTE"),
                            ),
                          ],
                        ),
                        Spacer(),
                      ],
                    ),
                  ),
                  Container(
                    height: MediaQuery
                        .of(context)
                        .size
                        .height * _keyBoardPanelHeight,
                    color: Colors.grey[200],
                    child: Column(
                      children: [
                        IconButton(
                          icon: Icon(Icons.close),
                          onPressed: toggleKeyboardPanel,
                        ),
                        TextField(
                          onSubmitted: (text) =>
                              sendGeneralCommand("TYPE,$text"),
                          decoration: InputDecoration(
                            hintText: 'Type here...',
                            border: OutlineInputBorder(),
                          ),
                        ),
                        Expanded(
                          child: ListView(
                            scrollDirection: Axis.horizontal,
                            children: [
                              IconButton(
                                icon: Icon(Icons.backspace),
                                onPressed: () =>
                                    sendGeneralCommand("BACKSPACE"),
                              ),
                              IconButton(
                                icon: Icon(Icons.arrow_downward),
                                onPressed: () => hotKey("SHIFT"),
                              ),
                              IconButton(
                                icon: Icon(Icons.alt_route),
                                onPressed: () => hotKey("ALT"),
                              ),
                              IconButton(
                                icon: Icon(Icons.arrow_upward),
                                onPressed: () => hotKey("CTRL"),
                              ),
                              IconButton(
                                icon: Icon(Icons.escalator),
                                onPressed: () => hotKey("ESC"),
                              ),
                              IconButton(
                                icon: Icon(Icons.keyboard_tab),
                                onPressed: () => hotKey("TAB"),
                              ),
                              IconButton(
                                icon: Icon(Icons.copy),
                                onPressed: () =>
                                    sendGeneralCommand("HOTKEY_CTRL_C"),
                              ),
                              IconButton(
                                icon: Icon(Icons.paste),
                                onPressed: () =>
                                    sendGeneralCommand("HOTKEY_CTRL_V"),
                              ),
                              IconButton(
                                icon: Icon(Icons.dangerous),
                                onPressed: () =>
                                    sendGeneralCommand("HOTKEY_ALT_F4"),
                              ),
                              IconButton(
                                icon: Icon(Icons.undo),
                                onPressed: () =>
                                    sendGeneralCommand("HOTKEY_CTRL_Z"),
                              ),
                              IconButton(
                                icon: Icon(Icons.redo),
                                onPressed: () =>
                                    sendGeneralCommand("HOTKEY_CTRL_Y"),
                              )
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    height: MediaQuery
                        .of(context)
                        .size
                        .height * _appPanelHeight,
                    color: Colors.grey[200],
                    child: Column(
                      children: [
                        IconButton(
                          icon: Icon(Icons.close),
                          onPressed: toggleAppPanel,
                        ),
                        Expanded(
                          child: ListView.builder(
                            itemCount: runningApps.length,
                            itemBuilder: (context, index) {
                              var app = runningApps[index];
                              return GestureDetector(
                                onTap: () => opencloseApp(app['name']),
                                // Add onTap handler to focus the app
                                child: ListTile(
                                  leading: app['icon'] != null
                                      ? Image.memory(
                                      base64Decode(app['icon']))
                                      : Icon(Icons.apps),
                                  title: Text(app['name']),
                                ),
                              );
                            },
                          ),

                        ),
                      ],
                    ),
                  ),
                  Container(
                    height: MediaQuery
                        .of(context)
                        .size
                        .height * _mousePanelHeight,
                    color: Colors.grey[200],
                    child: Column(
                      children: [
                        IconButton(
                          icon: Icon(Icons.close),
                          onPressed: toggleMousePanel,
                        ),
                        Spacer(),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          children: [
                            GestureDetector(
                              onTap: _handleTap,
                              child: Icon(Icons.mouse),
                            ),
                            IconButton(
                              icon: Icon(Icons.mouse),
                              onPressed: () =>
                                  sendGeneralCommand("RIGHT_CLICK"),
                            ),
                            IconButton(
                              icon: Icon(Icons.mouse),
                              onPressed: () =>
                                  sendGeneralCommand("MIDDLE_CLICK"),
                            ),
                            IconButton(
                              icon: Icon(Icons.arrow_upward_sharp),
                              onPressed: () =>
                                  sendGeneralCommand("SCROLL_UP"),
                            ),
                            IconButton(
                              icon: Icon(Icons.arrow_downward_sharp),
                              onPressed: () =>
                                  sendGeneralCommand("SCROLL_DOWN"),
                            ),
                          ],
                        ),
                        Spacer(),
                      ],
                    ),
                  ),
                  Container
                    (
                    height: MediaQuery
                        .of(context)
                        .size
                        .height * _webPanelHeight,
                    color: Colors.grey[200],
                    child: Column(
                      children: [
                        IconButton(
                          icon: Icon(Icons.close),
                          onPressed: toggleWebPanel,
                        ),
                        Expanded(
                          child: ListView(
                            scrollDirection: Axis.horizontal,
                            children: [
                              IconButton(
                                icon: Icon(Icons.add_box),
                                onPressed: () => sendGeneralCommand("WB_OT"),
                              ),
                              IconButton(
                                icon: Icon(
                                    Icons.indeterminate_check_box_rounded),
                                onPressed: () => sendGeneralCommand("WB_CT"),
                              ),
                              IconButton(
                                icon: Icon(Icons.refresh),
                                onPressed: () => sendGeneralCommand("WB_RE"),
                              ),
                              IconButton(
                                icon: Icon(Icons.arrow_forward),
                                onPressed: () => sendGeneralCommand("WB_NXT"),
                              ),
                              IconButton(
                                icon: Icon(Icons.arrow_back),
                                onPressed: () => sendGeneralCommand("WB_PRE"),
                              ),
                              IconButton(
                                icon: Icon(Icons.one_k),
                                onPressed: () => sendGeneralCommand("WB_1"),
                              ),
                              IconButton(
                                icon: Icon(Icons.two_k),
                                onPressed: () => sendGeneralCommand("WB_2"),
                              ),
                              IconButton(
                                icon: Icon(Icons.three_k),
                                onPressed: () => sendGeneralCommand("WB_3"),
                              ),
                              IconButton(
                                icon: Icon(Icons.four_k),
                                onPressed: () => sendGeneralCommand("WB_4"),
                              ),
                              IconButton(
                                icon: Icon(Icons.five_k),
                                onPressed: () => sendGeneralCommand("WB_5"),
                              ),
                              IconButton(
                                icon: Icon(Icons.six_k),
                                onPressed: () => sendGeneralCommand("WB_6"),
                              ),
                              IconButton(
                                icon: Icon(Icons.seven_k),
                                onPressed: () => sendGeneralCommand("WB_7"),
                              ),
                              IconButton(
                                icon: Icon(Icons.eight_k),
                                onPressed: () => sendGeneralCommand("WB_8"),
                              ),
                              IconButton(
                                icon: Icon(Icons.nine_k),
                                onPressed: () => sendGeneralCommand("WB_9"),
                              )
                            ],
                          ),
                        ),
                        Expanded(child:
                        ListView
                          (
                          scrollDirection: Axis.horizontal,
                          children: [
                            IconButton(
                              icon: Icon(Icons.play_circle_sharp),
                              onPressed: () => sendGeneralCommand("YT"),
                            ),
                            IconButton(
                              icon: Icon(Icons.android),
                              onPressed: () => sendGeneralCommand("CG"),
                            ),
                          ],
                        )
                        )
                      ],
                    ),
                  ),
                  Container(
                    height: MediaQuery
                        .of(context)
                        .size
                        .height * _quickPanelHeight,
                    color: Colors.grey[200],
                    child: Column(
                      children: [
                        IconButton(
                          icon: Icon(Icons.close),
                          onPressed: toggleQuickLaunch,
                        ),
                        TextField(
                          onSubmitted: (text) =>
                              sendGeneralCommand("START,$text"),
                          decoration: InputDecoration(
                            hintText: 'Type here...',
                            border: OutlineInputBorder(),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    // Dispose of the WebSocket channels when done
    generalChannel?.sink.close();
    mouseChannel?.sink.close();
    appChannel?.sink.close();
    super.dispose();
  }
}
