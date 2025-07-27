using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class MediapipeReceiver : MonoBehaviour
{
    public int port = 62345;
    private UdpClient udpClient;
    private Thread receiveThread;
    private bool running = false;
    public string lastJson = null;

    void Start()
    {
        udpClient = new UdpClient(port);
        running = true;
        receiveThread = new Thread(ReceiveData);
        receiveThread.IsBackground = true;
        receiveThread.Start();
        Debug.Log($"UDP监听端口: {port}");
    }

    void ReceiveData()
    {
        while (running)
        {
            try
            {
                IPEndPoint remoteEP = new IPEndPoint(IPAddress.Any, port);
                byte[] data = udpClient.Receive(ref remoteEP);
                string json = Encoding.UTF8.GetString(data);
                lastJson = json; // 只在主线程打印
            }
            catch (Exception ex)
            {
                Debug.LogError($"UDP接收异常: {ex.Message}");
            }
        }
    }

    void Update()
    {
        if (!string.IsNullOrEmpty(lastJson))
        {
            Debug.Log($"收到数据: {lastJson}");
            lastJson = null;
        }
    }

    void OnApplicationQuit()
    {
        running = false;
        if (receiveThread != null && receiveThread.IsAlive)
            receiveThread.Abort();
        if (udpClient != null)
            udpClient.Close();
    }
}