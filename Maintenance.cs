using System;
using System.IO;
using System.Diagnostics;
using System.Management;
using System.Threading;
class Maintenance {
 static bool Under(string file,string root){return !String.IsNullOrEmpty(file)&&Path.GetFullPath(file).StartsWith(Path.GetFullPath(root).TrimEnd('\\')+"\\",StringComparison.OrdinalIgnoreCase);}
 static int Main(string[] roots){
  try{
   foreach(string root in roots){
    string pact=Path.Combine(root,"PACT.exe");
    if(File.Exists(pact)){using(Process p=Process.Start(new ProcessStartInfo(pact,"--shutdown"){UseShellExecute=false,CreateNoWindow=true})){if(!p.WaitForExit(5000))p.Kill();}}
   }
   using(var search=new ManagementObjectSearcher("SELECT ProcessId,ExecutablePath FROM Win32_Process")){
    foreach(ManagementObject entry in search.Get()){
     string path=entry["ExecutablePath"] as string;bool match=false;foreach(string root in roots)if(Under(path,root))match=true;
     if(!match)continue;
     try{using(Process p=Process.GetProcessById(Convert.ToInt32(entry["ProcessId"]))){p.CloseMainWindow();if(!p.WaitForExit(2500)){p.Kill();if(!p.WaitForExit(5000))return 2;}}}catch(ArgumentException){}catch(InvalidOperationException){}
    }
   }return 0;
  }catch{return 3;}
 }
}
