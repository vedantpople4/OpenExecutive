import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="page">
      <h1>Not found</h1>
      <p>
        <Link to="/">Go back to a new decision</Link>
      </p>
    </div>
  )
}
