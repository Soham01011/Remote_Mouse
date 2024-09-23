import 'package:flutter/material.dart';
import 'connection_page.dart';
import 'joystick_page.dart';

void main() {
  runApp(MyApp());
  debugShowCheckedModeBanner: false;
}

class MyApp extends StatelessWidget {

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Remote Mouse',
      initialRoute: '/',
      routes: {
        '/': (context) => ConnectionPage(), // Pass MainFunctions to ConnectionPage
      },
    );
  }
}
