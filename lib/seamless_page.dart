import 'dart:async'; // For Timer
import 'dart:typed_data'; // For Uint8List
import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // For forcing landscape and fullscreen
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:perfect_volume_control/perfect_volume_control.dart'; // Import perfect_volume_control
import 'dart:ui' as ui; // For handling ui.Image

class SeamlessModePage extends StatefulWidget {
  final String ipAddress;

  SeamlessModePage({required this.ipAddress});

  @override
  _SeamlessModePageState createState() => _SeamlessModePageState();
}

class _SeamlessModePageState extends State<SeamlessModePage> {
  late WebSocketChannel _screenMirrorChannel;
  late WebSocketChannel _mouseControlChannel;
  Image? _image;
  Timer? _pingTimer;

  double screenWidth = 0;  // Server screen resolution width
  double screenHeight = 0; // Server screen resolution height

  @override
  void initState() {
    super.initState();
    _image = Image.asset(
      'assets/placeholder.png',
      gaplessPlayback: true,
    );

    // Initialize WebSocket connections
    _connectToScreenMirroring();
    _connectToMouseControl();

    // Start sending ping messages periodically to keep the connection alive
    _startKeepAlivePing();

    // Force landscape mode and fullscreen
    _setLandscapeAndFullscreen();

    // Initialize volume control
    _initializeVolumeControl();
  }

  void _connectToScreenMirroring() {
    _screenMirrorChannel = IOWebSocketChannel.connect('ws://${widget.ipAddress}:9996/screen_mirror');
    _screenMirrorChannel.stream.listen(_onImageReceived, onDone: _onConnectionDone, onError: _onConnectionError);
  }

  void _connectToMouseControl() {
    _mouseControlChannel = IOWebSocketChannel.connect('ws://${widget.ipAddress}:9996/mouse');
  }

  void _onImageReceived(dynamic message) async {
    if (message is List<int>) {
      final Uint8List imageBytes = Uint8List.fromList(message);
      final image = await _decodeImageFromBytes(imageBytes);

      setState(() {
        _image = Image.memory(
          imageBytes,
          fit: BoxFit.fill,  // Stretch image to fill the container (can distort aspect ratio)
        );

        // Update the screen dimensions based on the image size
        screenWidth = image.width.toDouble();
        screenHeight = image.height.toDouble();
        print("Image resolution received: ${screenWidth}x${screenHeight}");
      });
    }
  }

  Future<ui.Image> _decodeImageFromBytes(Uint8List bytes) async {
    final codec = await ui.instantiateImageCodec(bytes);
    final frame = await codec.getNextFrame();
    return frame.image;
  }

  void _onConnectionDone() {
    print('Screen mirroring connection closed.');
    _reconnectScreenMirroring();
  }

  void _onConnectionError(error) {
    print('Screen mirroring connection error: $error');
    _reconnectScreenMirroring();
  }

  void _reconnectScreenMirroring() {
    _pingTimer?.cancel();
    Future.delayed(Duration(seconds: 5), () {
      _connectToScreenMirroring();
      _startKeepAlivePing();
    });
  }

  void _onMouseControlError(error) {
    print('Mouse control connection error: $error');
    _reconnectMouseControl();
  }

  void _reconnectMouseControl() {
    Future.delayed(Duration(seconds: 5), () {
      _connectToMouseControl();
    });
  }

  void _startKeepAlivePing() {
    _pingTimer = Timer.periodic(Duration(seconds: 10), (_) {
      if (_screenMirrorChannel != null) {
        try {
          _screenMirrorChannel.sink.add('ping');
          print('Ping sent');
        } catch (e) {
          print('Ping failed: $e');
        }
      }
    });
  }

  void _setLandscapeAndFullscreen() {
    // Force landscape orientation and hide system UI for fullscreen mode
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.landscapeRight,
      DeviceOrientation.landscapeLeft,
    ]);
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  }

  Map<String, double> _calculateNormalizedCoordinates(Offset globalPosition, RenderBox renderBox) {
    final localPosition = renderBox.globalToLocal(globalPosition);

    final double localX = localPosition.dx;
    final double localY = localPosition.dy;

    final double deviceWidth = renderBox.size.width;
    final double deviceHeight = renderBox.size.height;

    // Calculate normalized coordinates accounting for landscape orientation
    final double normalizedX = localX / deviceWidth; // Normalized X remains the same
    final double normalizedY = (localY / deviceHeight); // Normalized Y remains as is

    return {
      'x': normalizedX,
      'y': normalizedY,
    };
  }

  void _sendVolumeCommand(String command) {
    print('Sending volume command: $command');
    _mouseControlChannel.sink.add(command); // Use the general channel for volume control
  }

  void _initializeVolumeControl() {
    PerfectVolumeControl.stream.listen((volume) {
      final double currentVolume = volume;
      final String command = (volume > currentVolume) ? 'VOLUME_UP' : 'VOLUME_DOWN';
      _sendVolumeCommand(command);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: GestureDetector(
          onScaleUpdate: (details) {
            if (details.scale == 1.0) {
              // Two-finger scroll (no scaling, just movement)
              if (details.focalPointDelta.dy < 0) {
                print("Two-finger swipe up - scroll up");
                _mouseControlChannel.sink.add('SCROLL,UP');
              } else if (details.focalPointDelta.dy > 0) {
                print("Two-finger swipe down - scroll down");
                _mouseControlChannel.sink.add('SCROLL,DOWN');
              }
            }
          },
          onScaleEnd: (ScaleEndDetails details) {
            _mouseControlChannel.sink.add('DRAG_END');
          },
          onTapDown: (TapDownDetails details) {
            final RenderBox renderBox = context.findRenderObject() as RenderBox;
            final coords = _calculateNormalizedCoordinates(details.globalPosition, renderBox);
            final double flippedX = coords['x']!;
            final double flippedY = coords['y']!;

            print('Single tap normalized coordinates: ($flippedX, $flippedY)');

            // Send single tap coordinates to WebSocket
            _mouseControlChannel.sink.add('MOUSE_CLICK,$flippedX,$flippedY');
          },
          onDoubleTapDown: (TapDownDetails details) {
            final RenderBox renderBox = context.findRenderObject() as RenderBox;
            final coords = _calculateNormalizedCoordinates(details.globalPosition, renderBox);
            final double flippedX = coords['x']!;
            final double flippedY = coords['y']!;

            print('Double tap normalized coordinates: ($flippedX, $flippedY)');

            // Send double tap coordinates to WebSocket
            _mouseControlChannel.sink.add('MOUSE_DOUBLE_CLICK,$flippedX,$flippedY');
          },
          onLongPress: () {
            // Handle long press for right-click
            final RenderBox renderBox = context.findRenderObject() as RenderBox;
            final TapDownDetails dummyDetails = TapDownDetails(
              globalPosition: renderBox.localToGlobal(Offset.zero),
              localPosition: renderBox.localToGlobal(Offset.zero),
            );
            final normalizedCoords = _calculateNormalizedCoordinates(dummyDetails, context);

            print('Long press at: (${normalizedCoords['x']}, ${normalizedCoords['y']}) - Simulating right click');
            _mouseControlChannel.sink.add('MOUSE_RIGHT_CLICK,${normalizedCoords['x']},${normalizedCoords['y']}');
          },
          child: Container(
            width: double.infinity,  // Ensure the container takes full width
            height: double.infinity,
            color: Colors.black,// Ensure the container takes full height
            child: _image ?? CircularProgressIndicator(), // Show image or loader
          ),
        ),
      ),
    );
  }

  void _sendMouseDragUpdateCommand(Offset focalPoint, RenderBox renderBox) {
    final coords = _calculateNormalizedCoordinates(focalPoint, renderBox);
    final double flippedX = coords['x']!;
    final double flippedY = coords['y']!;

    print('Drag move normalized coordinates: ($flippedX, $flippedY)');

    // Send drag move coordinates to WebSocket
    _mouseControlChannel.sink.add('DRAG_MOVE,$flippedX,$flippedY');
  }

  @override
  void dispose() {
    _pingTimer?.cancel();
    _screenMirrorChannel.sink.close();
    _mouseControlChannel.sink.close();
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);  // Restore UI mode on exit
    SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);  // Restore portrait mode on exit
    super.dispose();
  }
}
