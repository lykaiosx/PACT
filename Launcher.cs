using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
[assembly:AssemblyTitle("PACT")]
[assembly:AssemblyProduct("PACT")]
[assembly:AssemblyVersion("1.3.1.0")]
class Launcher {
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode)]static extern IntPtr CreateJobObject(IntPtr attr,string name);
 [DllImport("kernel32.dll")]static extern bool SetInformationJobObject(IntPtr job,int type,IntPtr data,uint size);
 [DllImport("kernel32.dll")]static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
 [DllImport("kernel32.dll")]static extern bool CloseHandle(IntPtr handle);
 [StructLayout(LayoutKind.Sequential)]struct Basic {public long a,b;public uint flags;public UIntPtr min,max;public uint active;public UIntPtr affinity;public uint priority,scheduling;}
 [StructLayout(LayoutKind.Sequential)]struct IO {public ulong a,b,c,d,e,f;}
 [StructLayout(LayoutKind.Sequential)]struct Extended {public Basic basic;public IO io;public UIntPtr a,b,c,d;}
 [STAThread]static int Main(string[] args){
  string root=AppDomain.CurrentDomain.BaseDirectory;
  try{
   string arguments="\""+Path.Combine(root,"app","app.py")+"\"";
   foreach(string a in args){if(a=="--hidden"||a=="--shutdown"||a=="--self-test")arguments+=" "+a;}
   ProcessStartInfo info=new ProcessStartInfo(Path.Combine(root,"runtime","PACT.exe"),arguments);
   info.WorkingDirectory=root;info.UseShellExecute=false;info.CreateNoWindow=true;
   IntPtr job=CreateJobObject(IntPtr.Zero,null);Extended limits=new Extended();limits.basic.flags=0x2000;
   int size=Marshal.SizeOf(limits);IntPtr memory=Marshal.AllocHGlobal(size);Marshal.StructureToPtr(limits,memory,false);SetInformationJobObject(job,9,memory,(uint)size);Marshal.FreeHGlobal(memory);
   using(Process p=Process.Start(info)){AssignProcessToJobObject(job,p.Handle);p.WaitForExit();int result=p.ExitCode;CloseHandle(job);return result;}
  }catch(Exception e){System.Windows.Forms.MessageBox.Show("PACT could not start. Please rerun the installer.\n"+e.Message,"PACT");return 1;}
 }
}
