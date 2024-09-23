import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'joystick_page.dart';

class ConnectionPage extends StatefulWidget {
  @override
  _ConnectionScreenPage createState() => _ConnectionScreenPage();
}

class _ConnectionScreenPage extends State<ConnectionPage> {
  WebSocketChannel? generalChannel;
  bool isConnected = false;
  List<String> availableServers = [];
  TextEditingController _ipController = TextEditingController();
  TextEditingController _passwordController = TextEditingController();

  @override
  void initState() {
    super.initState();
    startListeningForBroadcasts();  // Start listening for UDP broadcasts
  }

  void startListeningForBroadcasts() async {
    RawDatagramSocket.bind(InternetAddress.anyIPv4, 9995).then((socket) {
      socket.listen((RawSocketEvent event) {
        if (event == RawSocketEvent.read) {
          Datagram? datagram = socket.receive();
          if (datagram != null) {
            String message = String.fromCharCodes(datagram.data);
            setState(() {
              // Add server information (IP and Device name) to the list
              if (!availableServers.contains(message)) {
                availableServers.add(message);
              }
            });
          }
        }
      });
    });
  }

  void connectToServer(String ipAddress, String password) {
    if (ipAddress.isNotEmpty && password.isNotEmpty) {
      generalChannel = IOWebSocketChannel.connect('ws://$ipAddress:9999/auth');
      generalChannel!.sink.add(jsonEncode({"password": password}));

      generalChannel!.stream.listen((message) {
        var response = jsonDecode(message);
        if (response['status'] == "authenticated") {
          setState(() {
            isConnected = true;
          });

          // Pass ipAddress to JoystickPage when navigating
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => JoystickPage(ipAddress: ipAddress),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Authentication Failed')),
          );
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Remote Mouse V2"),
      ),
      body: Column(
        children: [
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  TextField(
                    controller: _ipController,
                    decoration: InputDecoration(labelText: "Enter IP address manually"),
                  ),
                  SizedBox(height: 20),
                  TextField(
                    controller: _passwordController,
                    decoration: InputDecoration(
                      labelText: "Enter Password",
                    ),
                    obscureText: true,
                  ),
                  SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: () {
                      connectToServer(_ipController.text, _passwordController.text);
                    },
                    child: Text(isConnected ? 'Connected' : 'Connect'),
                  ),
                  SizedBox(height: 20),
                  // Display list of available servers
                  Expanded(
                    child: ListView.builder(
                      itemCount: availableServers.length,
                      itemBuilder: (context, index) {
                        // Extract details from the broadcast message
                        String serverInfo = availableServers[index];

                        // Parse device name, IP address, and password
                        String ipAddress = serverInfo.split(",")[0].split(":")[1].trim();
                        String deviceName = serverInfo.split(",")[1].split(":")[1].trim();
                        String password = serverInfo.split(",")[2].split(":")[1].trim();

                        return ListTile(
                          title: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,  // Align text to the left
                            children: [
                              Text(
                                deviceName,  // Display the device name
                                style: TextStyle(
                                  fontSize: 18,  // Larger font size for device name
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              SizedBox(height: 4),  // Space between the device name and IP
                              Text(
                                ipAddress,  // Display the IP address
                                style: TextStyle(
                                  fontSize: 14,  // Smaller font size for IP address
                                  color: Colors.grey,  // Optional: grey color for IP address
                                ),
                              ),
                            ],
                          ),
                          onTap: () {
                            // Attempt connection to the server using IP address and password
                            connectToServer(ipAddress, password);
                          },
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),
          // Text at the bottom
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Text(
              'Developed by Soham Dalvi',
              style: TextStyle(
                fontSize: 20,
                color: Colors.lightBlue,
              ),
            ),
          ),
        ],
      ),
    );
  }


  @override
  void dispose() {
    _ipController.dispose();
    _passwordController.dispose();
    generalChannel?.sink.close();
    super.dispose();
  }
}
