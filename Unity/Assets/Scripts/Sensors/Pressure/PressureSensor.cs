using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class PressureSensor : MonoBehaviour
{
    private UdpClient udpClient;
    private Thread udpListenerThread;
    private bool isListening = false;
    private string receivedData = "";
    
    [SerializeField] private int listenPort = 2129;
    
    void Start()
    {
        StartUDPListener();
    }
    
    void StartUDPListener()
    {
        try
        {
            udpClient = new UdpClient(listenPort);
            isListening = true;
            
            udpListenerThread = new Thread(new ThreadStart(ListenForUDPData))
            {
                IsBackground = true
            };
            udpListenerThread.Start();
            
            Debug.Log($"UDP监听器启动，端口: {listenPort}");
        }
        catch (Exception e)
        {
            Debug.LogError("启动UDP监听器失败: " + e.Message);
        }
    }
    
    void ListenForUDPData()
    {
        while (isListening)
        {
            try
            {
                IPEndPoint remoteEndPoint = new IPEndPoint(IPAddress.Any, 0);
                byte[] data = udpClient.Receive(ref remoteEndPoint);
                string message = Encoding.UTF8.GetString(data);
                
                // 在主线程中处理数据
                receivedData = message;
                
            }
            catch (Exception e)
            {
                if (isListening)
                {
                    Debug.LogError("UDP接收错误: " + e.Message);
                }
            }
        }
    }
    
    void Update()
    {
        // 在主线程中处理接收到的数据
        if (!string.IsNullOrEmpty(receivedData))
        {
            Debug.Log("接收到串口数据: " + receivedData);
            ProcessSerialData(receivedData);
            receivedData = ""; // 清空数据
        }
    }
    
    void ProcessSerialData(string data)
    {
        // 在这里处理你的串口数据
        // 例如：解析传感器数据、控制游戏对象等
        
        // 示例：如果数据是数字，可以用来控制物体位置
        if (float.TryParse(data, out float value))
        {
            // 使用数据控制游戏对象
            transform.position = new Vector3(value, transform.position.y, transform.position.z);
        }
    }
    
    void OnDestroy()
    {
        StopUDPListener();
    }
    
    void OnApplicationQuit()
    {
        StopUDPListener();
    }
    
    void StopUDPListener()
    {
        isListening = false;
        
        if (udpListenerThread != null)
        {
            udpListenerThread.Abort();
        }
        
        if (udpClient != null)
        {
            udpClient.Close();
        }
        
        Debug.Log("UDP监听器已停止");
    }
}