"use client"

import React from 'react'

interface FaceData {
  name: string;
  confidence: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface FaceCoordinatesTableProps {
  faces: FaceData[];
}

const FaceCoordinatesTable: React.FC<FaceCoordinatesTableProps> = ({ faces }) => {
  if (!faces || faces.length === 0) return null;
  
  return (
    <div className="bg-gray-800 p-2 rounded-md mb-2">
      <h3 className="text-cyan-400 text-sm font-bold mb-2">人臉坐標表</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left text-gray-300">
          <thead className="text-xs text-gray-400 uppercase bg-gray-700">
            <tr>
              <th className="px-2 py-1">名稱</th>
              <th className="px-2 py-1">X</th>
              <th className="px-2 py-1">Y</th>
              <th className="px-2 py-1">寬度</th>
              <th className="px-2 py-1">高度</th>
              <th className="px-2 py-1">置信度</th>
            </tr>
          </thead>
          <tbody>
            {faces.map((face, index) => (
              <tr key={index} className="border-b border-gray-700">
                <td className="px-2 py-1">{face.name || '未知'}</td>
                <td className="px-2 py-1">{Math.round(face.x)}</td>
                <td className="px-2 py-1">{Math.round(face.y)}</td>
                <td className="px-2 py-1">{Math.round(face.width)}</td>
                <td className="px-2 py-1">{Math.round(face.height)}</td>
                <td className="px-2 py-1">{Math.round(face.confidence * 100)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default FaceCoordinatesTable
