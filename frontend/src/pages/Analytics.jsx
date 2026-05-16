import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { BarChart, Bar, AreaChart, Area, PieChart, Pie, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Download, TrendingUp } from 'lucide-react';

const Analytics = () => {
  const { token } = useAuth();
  const [days, setDays] = useState(7);
  const [data, setData] = useState({ daily: [], people_stats: [], hourly: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await fetch(`/api/analytics?days=${days}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const apiData = await res.json();
          
          // Format daily data from real API
          const formattedDaily = (apiData.daily_data || []).map(d => ({
            name: new Date(d.date).toLocaleDateString('en-US', { weekday: 'short' }),
            Recognitions: d.count,
            Threats: d.threats || 0
          }));

          setData({
            daily: formattedDaily,
            people_stats: apiData.people_stats || [],
            hourly: apiData.hourly_data || []
          });
        }
      } catch (err) {
        console.error("Failed to load analytics");
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [token, days]);

  const COLORS = ['#2f81f7', '#238636', '#d29922', '#cf222e', '#8957e5', '#db61a2'];

  return (
    <div className="analytics">
      <div className="page-header">
        <div>
          <h1>Intelligence Analytics</h1>
          <p className="page-subtitle">Real data from recognition and attendance systems</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <select className="input" value={days} onChange={e => setDays(Number(e.target.value))}>
            <option value={7}>Last 7 Days</option>
            <option value={14}>Last 14 Days</option>
            <option value={30}>Last 30 Days</option>
          </select>
        </div>
      </div>

      <div className="grid-dashboard">
        {/* Main Area Chart - Real daily data */}
        <div className="glass-card" style={{ gridColumn: '1 / -1' }}>
          <div className="section-header">
            <div className="section-title"><TrendingUp size={16} style={{ marginRight: '8px' }} /> Attendance & Threat Trend</div>
          </div>
          <div style={{ height: '300px', width: '100%', marginTop: '20px' }}>
            {data.daily.length === 0 ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
                <p>No data yet. Use the Attendance module to generate real attendance records.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.daily}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-default)" vertical={false} />
                  <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickMargin={10} />
                  <YAxis stroke="var(--text-muted)" fontSize={12} tickMargin={10} />
                  <Tooltip 
                    contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-sm)' }}
                    itemStyle={{ color: 'var(--text-primary)', fontSize: '0.85rem' }}
                  />
                  <Legend />
                  <Area type="monotone" dataKey="Recognitions" stackId="1" stroke="var(--accent-blue)" fill="rgba(47, 129, 247, 0.2)" strokeWidth={2} />
                  <Area type="monotone" dataKey="Threats" stackId="2" stroke="var(--danger)" fill="rgba(218, 54, 51, 0.2)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Recognition Distribution - Real per-person stats */}
        <div className="glass-card">
          <div className="section-header">
            <div className="section-title">Recognition Distribution</div>
          </div>
          <div style={{ height: '250px', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {data.people_stats.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center' }}>
                <p>No recognition data yet.</p>
                <p style={{ fontSize: '0.8rem' }}>Enroll people and use the monitor to generate recognition stats.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.people_stats}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {data.people_stats.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-sm)' }}
                    itemStyle={{ color: 'var(--text-primary)', fontSize: '0.85rem' }}
                  />
                  <Legend iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Hourly Activity - Real data */}
        <div className="glass-card">
          <div className="section-header">
            <div className="section-title">Today's Hourly Activity</div>
          </div>
          <div style={{ height: '250px', width: '100%' }}>
            {data.hourly.length === 0 ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
                <p>No hourly data recorded today.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.hourly}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-default)" vertical={false} />
                  <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={12} tickMargin={10} />
                  <Tooltip 
                    contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-sm)' }}
                    cursor={{ fill: 'var(--bg-elevated)' }}
                  />
                  <Bar dataKey="traffic" fill="var(--success)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
