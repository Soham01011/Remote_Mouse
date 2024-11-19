import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // For forcing landscape and fullscreen
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:ui' as ui;

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
  }

  void _connectToScreenMirroring() {
    _screenMirrorChannel = IOWebSocketChannel.connect('ws://${widget.ipAddress}:9996/screen_mirror');
    _screenMirrorChannel.stream.listen(
      _onImageReceived,
      onDone: _onConnectionDone,
      onError: _onConnectionError,
    );
  }

  void _connectToMouseControl() {
    _mouseControlChannel = IOWebSocketChannel.connect('ws://${widget.ipAddress}:9996/mouse');
  }

  void _onImageReceived(dynamic message) async {
    if (message is List<int>) {
      final Uint8List imageBytes = Uint8List.fromList(message);

      setState(() {
        _image = Image.memory(
          imageBytes,
          fit: BoxFit.fill, // Adjust to fill the screen
          gaplessPlayback: true,
        );
      });
    }
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

  void _startKeepAlivePing() {
    _pingTimer = Timer.periodic(Duration(seconds: 10), (_) {
      try {
        _screenMirrorChannel.sink.add('ping');
        print('Ping sent');
      } catch (e) {
        print('Ping failed: $e');
      }
    });
  }

  void _setLandscapeAndFullscreen() {
    SystemChrome.setPreferredOrientations([DeviceOrientation.landscapeRight, DeviceOrientation.landscapeLeft]);
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  }

  Map<String, double> _calculateNormalizedCoordinates(Offset globalPosition, RenderBox renderBox) {
    final localPosition = renderBox.globalToLocal(globalPosition);

    final double localX = localPosition.dx;
    final double localY = localPosition.dy;

    final double deviceWidth = renderBox.size.width;
    final double deviceHeight = renderBox.size.height;

    final double normalizedX = localX / deviceWidth; // Normalized based on device screen width
    final double normalizedY = localY / deviceHeight; // Normalized based on device screen height

    return {
      'x': normalizedX,
      'y': normalizedY,
    };
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: GestureDetector(
          onTapDown: (TapDownDetails details) {
            final RenderBox renderBox = context.findRenderObject() as RenderBox;
            final coords = _calculateNormalizedCoordinates(details.globalPosition, renderBox);

            final double normalizedX = coords['x']!;
            final double normalizedY = coords['y']!;

            print('Single tap normalized coordinates: ($normalizedX, $normalizedY)');
            _mouseControlChannel.sink.add('MOUSE_CLICK,$normalizedX,$normalizedY');
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
          onPanUpdate: (details) {
            final RenderBox renderBox = context.findRenderObject() as RenderBox;
            final coords = _calculateNormalizedCoordinates(details.globalPosition, renderBox);

            final double normalizedX = coords['x']!;
            final double normalizedY = coords['y']!;

            print('Pan update normalized coordinates: ($normalizedX, $normalizedY)');
            _mouseControlChannel.sink.add('MOUSE_PAN,$normalizedX,$normalizedY');
          },
          onLongPress: () {
            print('Long press started');
            // Optionally, you can set some flag here or update state, but no action is sent.
          },
          onLongPressEnd: (details) {
            print('Long press ended');

            // Calculate normalized coordinates when long press ends
            final RenderBox renderBox = context.findRenderObject() as RenderBox;
            final Offset globalPosition = renderBox.globalToLocal(details.localPosition); // Get position at long press end
            final coords = _calculateNormalizedCoordinates(globalPosition, renderBox);

            final double normalizedX = coords['x']!;
            final double normalizedY = coords['y']!;

            print('Long press ended normalized coordinates: ($normalizedX, $normalizedY)');
            _mouseControlChannel.sink.add('MOUSE_CLICK_RIGHT,$normalizedX,$normalizedY'); // Send right-click with normalized coordinates
          },
          child: Container(
            width: double.infinity,
            height: double.infinity,
            color: Colors.black,
            child: _image ?? CircularProgressIndicator(),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _pingTimer?.cancel();
    _screenMirrorChannel.sink.close();
    _mouseControlChannel.sink.close();
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
    SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
    super.dispose();
  }
}
