using System;
using System.Reflection;
class MaintenanceTests {
 static int Main(string[] args){
  var assembly=Assembly.LoadFrom(args[0]);var method=assembly.GetType("Maintenance").GetMethod("Under",BindingFlags.NonPublic|BindingFlags.Static);
  string root=@"C:\test\PACT";
  string[] files={@"C:\test\PACT\PACT.exe",@"C:\test\PACT\runtime\PACT.exe",@"C:\test\PACT-other\PACT.exe",null,"invalid\0path"};
  bool[] expected={true,true,false,false,false};
  for(int i=0;i<files.Length;i++)if((bool)method.Invoke(null,new object[]{files[i],root})!=expected[i])return 1;
  Console.WriteLine("Installer path checks passed (5 cases).");return 0;
 }
}
