using UnityEngine;
using System;
using System.Net;
using System.Net.Sockets;
using System.Threading;

public class UDP_withIK : MonoBehaviour
{
    //public const string SERVER_IP = "192.168.31.176";  // 默认本地服务器IP
    public const string SERVER_IP = "127.0.0.1";  // 默认本地服务器IP
    private const int SERVER_PORT = 8080;          // 默认端口
    private const float UPDATE_RATE = 100f;        // 100Hz
    private const float RECONNECT_DELAY = 3f;      // 重连延迟（秒）
    public float startDelay = 2f;                  // 启动延迟（秒）

    private UdpClient udpClient;
    private IPEndPoint remoteEndPoint;
    private bool isRunning = true;

    // 引用GetJointAngle组件
    private GetJointAngle jointAngle;

    // 扭矩控制
    [Range(0f, 100f)]
    public float torqueValue = 0f;  // 默认扭矩值为100

    private byte[] data = new byte[85];
    private float[] angles = new float[20];
    private long frameCount = 0;
    private DateTime lastStatsTime;
    private string lastErrorMessage = null;
    private float nextUpdateTime = 0f;

    private void Start()
    {
        jointAngle = GetComponent<GetJointAngle>();
        if (jointAngle == null)
        {
            Debug.LogError("GetJointAngle组件未找到");
            return;
        }

        Application.targetFrameRate = 120;  // 设置更高的帧率以确保发送频率
        QualitySettings.vSyncCount = 0;    // 禁用垂直同步
        lastStatsTime = DateTime.Now;

        // 初始化UDP和数据包
        InitializeUDP();
        InitializeDataPacket();
    }

    private void InitializeUDP()
    {
        try
        {
            udpClient = new UdpClient();
            remoteEndPoint = new IPEndPoint(IPAddress.Parse(SERVER_IP), SERVER_PORT);
            Debug.Log($"UDP客户端初始化完成，目标地址：{SERVER_IP}:{SERVER_PORT}");
        }
        catch (Exception e)
        {
            Debug.LogError($"UDP客户端初始化失败: {e.Message}");
        }
    }

    private void InitializeDataPacket()
    {
        // 初始化帧头和长度
        data[0] = 0xAA;
        data[1] = 0xBB;
        data[2] = 16;
    }

    private void Update()
    {
        // 处理错误消息
        if (lastErrorMessage != null)
        {
            Debug.LogError(lastErrorMessage);
            lastErrorMessage = null;
        }

        if (!isRunning || jointAngle == null || udpClient == null) return;

        // 控制发送频率
        if (Time.time < nextUpdateTime) return;
        nextUpdateTime = Time.time + (1f / UPDATE_RATE);

        try
        {
            // 获取角度数据
            jointAngle.GetLeftHandAnglesArray(angles, 0);
            jointAngle.GetRightHandAnglesArray(angles, 8);

            // 处理扭矩值
            short torqueInt = (short)(torqueValue * 10);
            data[3] = (byte)(torqueInt & 0xFF);
            data[4] = (byte)(torqueInt >> 8);

            // 将角度数据写入缓冲区
            int offset = 5;
            for (int i = 0; i < 20; i++)
            {
                BitConverter.TryWriteBytes(new Span<byte>(data, offset + i * 4, 4), angles[i]);
            }

            // 发送数据
            udpClient.Send(data, data.Length, remoteEndPoint);
            frameCount++;

            // 每秒输出统计信息
            TimeSpan elapsed = DateTime.Now - lastStatsTime;
            if (elapsed.TotalSeconds >= 1.0)
            {
                float fps = frameCount / (float)elapsed.TotalSeconds;
                frameCount = 0;
                lastStatsTime = DateTime.Now;
            }
        }
        catch (Exception e)
        {
            lastErrorMessage = $"发送数据出错: {e.Message}";
            if (udpClient != null)
            {
                udpClient.Close();
                udpClient = null;
            }
        }
    }

    private void OnDestroy()
    {
        isRunning = false;
        if (udpClient != null)
        {
            try
            {
                udpClient.Close();
            }
            catch (Exception e)
            {
                Debug.LogError($"关闭UDP连接出错: {e.Message}");
            }
            finally
            {
                udpClient = null;
            }
        }
    }

    private void OnApplicationQuit()
    {
        isRunning = false;
    }
}
