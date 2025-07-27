using UnityEngine;

public class PathOnBone : MonoBehaviour
{
    [Header("直线路径设置")]
    [SerializeField] private string pathName = "直线路径";
    
    [Header("路径点（请将骨骼下的空物体拖进来）")]
    public Transform[] pathPoints;
    
    // 获取路径名称（用于显示）
    public string GetPathName() => pathName;
}