using UnityEngine;
using UnityEngine.XR;
using System.Collections.Generic;

public class TargetControl_Relative : MonoBehaviour
{
    [Header("控制设置")]
    public Transform targetObject;        // 目标物体
    public Transform vrController;        // VR控制器物体
    public bool useLeftController = false;  // 使用左手控制器（false为右手）
    
    [Header("控制参数")]
    public bool enablePosition = true;    // 是否启用位置控制
    public bool enableRotation = true;    // 是否启用旋转控制
    public float positionSensitivity = 1f;  // 位置灵敏度
    public float rotationSensitivity = 1f;  // 旋转灵敏度
    
    // 私有变量
    private bool isControlling = false;   // 是否正在控制
    private Vector3 initialControllerPos;  // 初始控制器位置
    private Quaternion initialControllerRot; // 初始控制器旋转
    private Vector3 initialTargetPos;     // 初始目标物体位置
    private Quaternion initialTargetRot;  // 初始目标物体旋转
    
    // XR控制器
    private InputDevice controller;
    
    void Start()
    {
        // 检查必要的组件
        if (targetObject == null)
        {
            Debug.LogError("目标物体未指定！请在Inspector中设置targetObject");
        }
        
        if (vrController == null)
        {
            Debug.LogError("VR控制器未指定！请在Inspector中设置vrController");
        }
        
        // 初始化控制器
        InitializeController();
    }

    void Update()
    {
        // 检查必要组件是否存在
        if (targetObject == null || vrController == null)
            return;
            
        // 检查控制器是否有效
        if (!controller.isValid)
        {
            InitializeController();
            return;
        }
        
        // 检测grip按钮状态
        bool gripPressed = false;
        if (controller.TryGetFeatureValue(CommonUsages.grip, out float gripValue))
        {
            gripPressed = gripValue > 0.5f; // 按钮按下阈值
        }
        
        // 按下grip按钮开始控制
        if (gripPressed && !isControlling)
        {
            StartControl();
        }
        // 松开grip按钮停止控制
        else if (!gripPressed && isControlling)
        {
            StopControl();
        }
        
        // 如果正在控制，更新目标物体位置和旋转
        if (isControlling)
        {
            UpdateTargetTransform();
        }
    }
    
    /// <summary>
    /// 初始化控制器
    /// </summary>
    void InitializeController()
    {
        List<InputDevice> devices = new List<InputDevice>();
        
        InputDeviceCharacteristics targetCharacteristics = useLeftController ? 
            InputDeviceCharacteristics.Left : InputDeviceCharacteristics.Right;
        
        InputDevices.GetDevicesWithCharacteristics(
            targetCharacteristics | InputDeviceCharacteristics.Controller, 
            devices);
        
        if (devices.Count > 0)
        {
            controller = devices[0];
            Debug.Log($"已连接{(useLeftController ? "左手" : "右手")}控制器: {controller.name}");
        }
        else
        {
            Debug.LogWarning($"未找到{(useLeftController ? "左手" : "右手")}控制器");
        }
    }
    
    /// <summary>
    /// 开始控制目标物体
    /// </summary>
    void StartControl()
    {
        isControlling = true;
        
        // 记录初始状态
        initialControllerPos = vrController.position;
        initialControllerRot = vrController.rotation;
        initialTargetPos = targetObject.position;
        initialTargetRot = targetObject.rotation;
        
        Debug.Log("开始控制目标物体");
    }
    
    /// <summary>
    /// 停止控制目标物体
    /// </summary>
    void StopControl()
    {
        isControlling = false;
        Debug.Log("停止控制目标物体");
    }
    
    /// <summary>
    /// 更新目标物体的位置和旋转
    /// </summary>
    void UpdateTargetTransform()
    {
        // 计算控制器的相对位置变化
        Vector3 controllerDeltaPos = vrController.position - initialControllerPos;
        
        // 计算控制器的相对旋转变化
        Quaternion controllerDeltaRot = vrController.rotation * Quaternion.Inverse(initialControllerRot);
        
        // 更新目标物体位置（如果启用位置控制）
        if (enablePosition)
        {
            targetObject.position = initialTargetPos + controllerDeltaPos * positionSensitivity;
        }
        
        // 更新目标物体旋转（如果启用旋转控制）
        if (enableRotation)
        {
            targetObject.rotation = controllerDeltaRot * initialTargetRot;
        }
    }
    
    /// <summary>
    /// 手动重置控制状态
    /// </summary>
    public void ResetControl()
    {
        isControlling = false;
        Debug.Log("手动重置控制状态");
    }
    
    /// <summary>
    /// 切换控制器（左手/右手）
    /// </summary>
    public void SetController(bool useLeft)
    {
        useLeftController = useLeft;
        InitializeController();
        Debug.Log($"控制器切换为: {(useLeft ? "左手" : "右手")}");
    }
    
    /// <summary>
    /// 获取当前grip按钮值（调试用）
    /// </summary>
    public float GetGripValue()
    {
        if (controller.isValid && controller.TryGetFeatureValue(CommonUsages.grip, out float gripValue))
        {
            return gripValue;
        }
        return 0f;
    }
}
